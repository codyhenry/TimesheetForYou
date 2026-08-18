from datetime import datetime, timedelta, time as dt_time
from decimal import Decimal, ROUND_CEILING
import re

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Exists, OuterRef, Prefetch
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import TimeEntry, TimesheetSubmission, TimesheetWeekLock, WeeklyTimesheet
from .pdf import render_timesheet_pdf


SUBMITTED_STATUSES = {
    WeeklyTimesheet.Status.SUBMITTED_FULLY_SIGNED,
    WeeklyTimesheet.Status.SUBMITTED_WITH_UNSIGNED_ENTRIES,
}
SATURDAY_WEEKDAY = 5
FRIDAY_WEEKDAY = 4
QUARTER_HOUR = Decimal("0.25")
REQUESTS_PER_INCENTIVE = 5
FILENAME_UNSAFE_CHARS = re.compile(r'[^A-Za-z0-9,._ -]+')


def get_timesheet_week_range(for_date):
    """Return the Saturday-Friday week containing for_date."""
    week_start = for_date - timedelta(days=(for_date.weekday() - SATURDAY_WEEKDAY) % 7)
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def _format_short_date_for_filename(value):
    return f"{value.month}.{value.day}.{value.year % 100:02d}"


def _safe_pdf_filename_part(value):
    cleaned = FILENAME_UNSAFE_CHARS.sub("", str(value or "")).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or "Unknown"


def format_timesheet_pdf_filename(timesheet):
    first_name = _safe_pdf_filename_part(timesheet.nanny.first_name or timesheet.nanny.username)
    last_name = _safe_pdf_filename_part(timesheet.nanny.last_name or timesheet.nanny.username)
    week_range = (
        f"{_format_short_date_for_filename(timesheet.week_start_date)}-"
        f"{_format_short_date_for_filename(timesheet.week_end_date)}"
    )
    return f"{last_name},{first_name} {week_range}.pdf"


def get_or_create_current_week_timesheet(user):
    week_start, week_end = get_timesheet_week_range(timezone.localdate())
    return WeeklyTimesheet.objects.get_or_create(
        nanny=user,
        week_start_date=week_start,
        defaults={"week_end_date": week_end},
    )


def calculate_total_hours(start_time, end_time):
    start_dt = datetime.combine(timezone.localdate(), start_time)
    end_dt = datetime.combine(timezone.localdate(), end_time)
    if end_dt <= start_dt:
        raise ValidationError(
            {"end_time": "End time must be after start time."})
    total_seconds = Decimal((end_dt - start_dt).total_seconds())
    raw_hours = total_seconds / Decimal("3600")
    rounded_quarters = (raw_hours / QUARTER_HOUR).to_integral_value(
        rounding=ROUND_CEILING
    )
    return (rounded_quarters * QUARTER_HOUR).quantize(Decimal("0.00"))


def get_timesheet_entry_prefetch():
    return Prefetch(
        "entries",
        queryset=TimeEntry.objects.select_related(
            "parent_signature").order_by("work_date", "start_time", "id"),
    )


def filter_submitted_timesheets(queryset, params):
    week_start = params.get("week_start")
    nanny = params.get("nanny")
    family = params.get("family")
    status_value = params.get("status")
    has_unsigned_entries = params.get("has_unsigned_entries")

    if week_start:
        queryset = queryset.filter(week_start_date=week_start)
    if nanny:
        queryset = queryset.filter(nanny_id=nanny)
    if family:
        queryset = queryset.filter(
            Exists(
                TimeEntry.objects.filter(
                    timesheet_id=OuterRef("pk"),
                    family_name__icontains=family,
                )
            )
        )
    if status_value:
        queryset = queryset.filter(status=status_value)
    if has_unsigned_entries in {True, "true", "True", "1", 1}:
        queryset = queryset.filter(
            Exists(
                TimeEntry.objects.filter(
                    timesheet_id=OuterRef("pk"),
                    signature_status__in=[
                        TimeEntry.SignatureStatus.UNSIGNED,
                        TimeEntry.SignatureStatus.SIGNATURE_INVALIDATED,
                    ],
                )
            )
        )
    elif has_unsigned_entries in {"false", "False", "0"}:
        queryset = queryset.exclude(
            Exists(
                TimeEntry.objects.filter(
                    timesheet_id=OuterRef("pk"),
                    signature_status__in=[
                        TimeEntry.SignatureStatus.UNSIGNED,
                        TimeEntry.SignatureStatus.SIGNATURE_INVALIDATED,
                    ],
                )
            )
        )
    return queryset.order_by("-week_start_date", "-submitted_at", "-id")


def is_timesheet_week_locked(timesheet):
    return TimesheetWeekLock.objects.filter(
        week_start_date=timesheet.week_start_date
    ).exists()


def ensure_timesheet_week_unlocked(timesheet):
    if is_timesheet_week_locked(timesheet):
        raise ValidationError(
            {"detail": "This timesheet week is locked and cannot be edited."}
        )


def lock_timesheet_week(week_start_date, locked_by=None, note=""):
    week_start, week_end = get_timesheet_week_range(week_start_date)
    week_lock, _ = TimesheetWeekLock.objects.get_or_create(
        week_start_date=week_start,
        defaults={
            "week_end_date": week_end,
            "locked_by": locked_by,
            "note": note or "",
        },
    )
    return week_lock


def get_requested_entries_for_nanny(nanny):
    return (
        TimeEntry.objects.filter(
            timesheet__nanny=nanny,
            family_requested_nanny=True,
        )
        .select_related("timesheet", "timesheet__nanny")
        .order_by("work_date", "timesheet__week_start_date", "id")
    )


def get_lifetime_request_count(nanny):
    return get_requested_entries_for_nanny(nanny).count()


def get_timesheet_request_count(timesheet):
    return timesheet.entries.filter(family_requested_nanny=True).count()


def get_requests_until_next_incentive(nanny):
    remainder = get_lifetime_request_count(nanny) % REQUESTS_PER_INCENTIVE
    if remainder == 0:
        return REQUESTS_PER_INCENTIVE
    return REQUESTS_PER_INCENTIVE - remainder


def _request_entry_summary(entry, request_number):
    timesheet = entry.timesheet
    return {
        "request_number": request_number,
        "entry_id": entry.id,
        "timesheet_id": timesheet.id,
        "work_date": entry.work_date.isoformat(),
        "family_name": entry.family_name,
        "week_start_date": timesheet.week_start_date.isoformat(),
        "week_end_date": timesheet.week_end_date.isoformat(),
    }


def get_request_incentive_groups_for_timesheet(timesheet):
    """Return lifetime request milestone groups earned by this timesheet.

    Incentives are earned on request numbers 5, 10, 15, etc. The group is
    attached to the timesheet containing the milestone request entry.
    """
    requested_entries = list(get_requested_entries_for_nanny(timesheet.nanny))
    groups = []

    for milestone_index in range(REQUESTS_PER_INCENTIVE - 1, len(requested_entries), REQUESTS_PER_INCENTIVE):
        milestone_entry = requested_entries[milestone_index]
        if milestone_entry.timesheet_id != timesheet.id:
            continue

        group_start = milestone_index - (REQUESTS_PER_INCENTIVE - 1)
        group_entries = requested_entries[group_start:milestone_index + 1]
        groups.append(
            {
                "incentive_number": (milestone_index + 1) // REQUESTS_PER_INCENTIVE,
                "milestone_request_number": milestone_index + 1,
                "milestone_entry_id": milestone_entry.id,
                "entries": [
                    _request_entry_summary(entry, group_start + offset + 1)
                    for offset, entry in enumerate(group_entries)
                ],
            }
        )
    return groups


def get_timesheet_request_incentive_count(timesheet):
    return len(get_request_incentive_groups_for_timesheet(timesheet))


def update_timesheet_status(timesheet):
    if timesheet.is_submitted or timesheet.submission_id or timesheet.submitted_at:
        return timesheet

    entries = list(timesheet.entries.only("signature_status"))
    if not entries:
        new_status = WeeklyTimesheet.Status.DRAFT
    else:
        signed_count = sum(
            1 for entry in entries if entry.signature_status == TimeEntry.SignatureStatus.SIGNED)
        if signed_count == len(entries):
            new_status = WeeklyTimesheet.Status.FULLY_SIGNED
        elif signed_count > 0:
            new_status = WeeklyTimesheet.Status.PARTIALLY_SIGNED
        else:
            new_status = WeeklyTimesheet.Status.DRAFT

    if new_status != timesheet.status:
        timesheet.status = new_status
        timesheet.save(update_fields=["status", "updated_at"])
    return timesheet


def invalidate_signature_if_needed(entry, changed_fields):
    tracked_fields = {"work_date", "family_name", "family_requested_nanny",
                      "start_time", "end_time", "total_hours", "notes"}
    if entry.signature_status != TimeEntry.SignatureStatus.SIGNED:
        return False
    if not tracked_fields.intersection(set(changed_fields)):
        return False
    entry.signature_status = TimeEntry.SignatureStatus.SIGNATURE_INVALIDATED
    entry.save(update_fields=["signature_status", "updated_at"])
    return True


def _build_submission_snapshot(timesheet, entries, total_hours):
    family_totals = {}
    for entry in entries:
        family_totals.setdefault(entry.family_name, Decimal("0.00"))
        family_totals[entry.family_name] += entry.total_hours
    return {
        "timesheet_id": timesheet.id,
        "nanny_id": timesheet.nanny_id,
        "is_late_submission": timesheet.is_late_submission,
        "late_submission_note": timesheet.late_submission_note,
        "nanny_name": timesheet.nanny.get_full_name() or timesheet.nanny.username,
        "week_start_date": timesheet.week_start_date.isoformat(),
        "week_end_date": timesheet.week_end_date.isoformat(),
        "total_hours": str(total_hours),
        "requested_entry_count": get_timesheet_request_count(timesheet),
        "request_incentive_count": get_timesheet_request_incentive_count(timesheet),
        "entries": [
            {
                "id": entry.id,
                "work_date": entry.work_date.isoformat(),
                "family_name": entry.family_name,
                "family_requested_nanny": entry.family_requested_nanny,
                "start_time": entry.start_time.isoformat(),
                "end_time": entry.end_time.isoformat(),
                "total_hours": str(entry.total_hours),
                "signature_status": entry.signature_status,
                "notes": entry.notes,
            }
            for entry in entries
        ],
        "family_totals": [{"family_name": name, "total_hours": str(hours)} for name, hours in family_totals.items()],
    }


def generate_timesheet_pdf(timesheet):
    return render_timesheet_pdf(timesheet)


def get_timesheet_submission_deadline(week_end_date):
    """Return the configured submission deadline for a given week.

    Default deadline is Saturday 12:00 (local timezone) after the Friday week end.
    """
    deadline_weekday = int(
        getattr(settings, "TIMESHEET_SUBMISSION_DEADLINE_WEEKDAY", SATURDAY_WEEKDAY))
    deadline_hour = int(
        getattr(settings, "TIMESHEET_SUBMISSION_DEADLINE_HOUR", 12))
    deadline_minute = int(
        getattr(settings, "TIMESHEET_SUBMISSION_DEADLINE_MINUTE", 0))

    candidate_date = week_end_date + timedelta(days=1)
    while candidate_date.weekday() != deadline_weekday:
        candidate_date += timedelta(days=1)

    naive_deadline = datetime.combine(candidate_date, dt_time(
        hour=deadline_hour, minute=deadline_minute))
    return timezone.make_aware(naive_deadline, timezone.get_current_timezone())


def is_late_submission(week_end_date, submitted_at):
    return submitted_at > get_timesheet_submission_deadline(week_end_date)


@transaction.atomic
def submit_timesheet(timesheet, submitted_by=None, force_late=False, late_submission_note=""):
    ensure_timesheet_week_unlocked(timesheet)
    entries = list(timesheet.entries.select_related("parent_signature").all())
    if not entries:
        raise ValidationError(
            {"detail": "A timesheet must have at least one entry before submission."})

    total_hours = sum(
        (entry.total_hours for entry in entries), Decimal("0.00"))
    has_unsigned_entries = any(
        entry.signature_status != TimeEntry.SignatureStatus.SIGNED for entry in entries)
    status = (
        WeeklyTimesheet.Status.SUBMITTED_WITH_UNSIGNED_ENTRIES
        if has_unsigned_entries
        else WeeklyTimesheet.Status.SUBMITTED_FULLY_SIGNED
    )
    timestamp = timezone.now()
    is_late = bool(force_late or is_late_submission(
        timesheet.week_end_date, timestamp))
    timesheet.status = status
    timesheet.submitted_at = timestamp
    timesheet.is_late_submission = is_late
    timesheet.late_submission_note = late_submission_note or ""
    pdf_bytes = generate_timesheet_pdf(timesheet)
    file_name = format_timesheet_pdf_filename(timesheet)
    snapshot = _build_submission_snapshot(timesheet, entries, total_hours)

    submission = timesheet.submission
    if submission is None:
        submission = TimesheetSubmission.objects.create(
            status=status,
            submitted_by=submitted_by or timesheet.nanny,
            is_late_submission=is_late,
            late_submission_note=late_submission_note or "",
            total_hours=total_hours,
            snapshot=snapshot,
        )
    else:
        if submission.pdf_file:
            submission.pdf_file.delete(save=False)
        submission.status = status
        submission.submitted_by = submitted_by or timesheet.nanny
        submission.submitted_at = timestamp
        submission.is_late_submission = is_late
        submission.late_submission_note = late_submission_note or ""
        submission.total_hours = total_hours
        submission.snapshot = snapshot
        submission.save(
            update_fields=[
                "status",
                "submitted_by",
                "submitted_at",
                "is_late_submission",
                "late_submission_note",
                "total_hours",
                "snapshot",
            ]
        )

    submission.pdf_file.save(file_name, ContentFile(pdf_bytes), save=True)

    if timesheet.pdf_file:
        timesheet.pdf_file.delete(save=False)
    timesheet.submission = submission
    timesheet.pdf_file.save(file_name, ContentFile(pdf_bytes), save=False)
    timesheet.save(
        update_fields=[
            "submission",
            "submitted_at",
            "status",
            "is_late_submission",
            "late_submission_note",
            "pdf_file",
            "updated_at",
        ]
    )
    return timesheet
