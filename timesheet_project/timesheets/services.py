from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Exists, OuterRef, Prefetch
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import TimeEntry, TimesheetSubmission, WeeklyTimesheet
from .pdf import render_timesheet_pdf


SUBMITTED_STATUSES = {
    WeeklyTimesheet.Status.SUBMITTED_FULLY_SIGNED,
    WeeklyTimesheet.Status.SUBMITTED_WITH_UNSIGNED_ENTRIES,
}
# Timesheet totals should round to the nearest hundredth of an hour using standard half-up rules.
HOUR_ROUNDING = ROUND_HALF_UP


def get_or_create_current_week_timesheet(user):
    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    return WeeklyTimesheet.objects.get_or_create(
        nanny=user,
        week_start_date=week_start,
        defaults={"week_end_date": week_end},
    )


def calculate_total_hours(start_time, end_time):
    start_dt = datetime.combine(timezone.localdate(), start_time)
    end_dt = datetime.combine(timezone.localdate(), end_time)
    if end_dt <= start_dt:
        raise ValidationError({"end_time": "End time must be after start time."})
    total_seconds = Decimal((end_dt - start_dt).total_seconds())
    hours = (total_seconds / Decimal("3600")).quantize(Decimal("0.01"), rounding=HOUR_ROUNDING)
    return hours


def get_timesheet_entry_prefetch():
    return Prefetch(
        "entries",
        queryset=TimeEntry.objects.select_related("parent_signature").order_by("work_date", "start_time", "id"),
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


def update_timesheet_status(timesheet):
    if timesheet.is_submitted or timesheet.submission_id or timesheet.submitted_at:
        return timesheet

    entries = list(timesheet.entries.only("signature_status"))
    if not entries:
        new_status = WeeklyTimesheet.Status.DRAFT
    else:
        signed_count = sum(1 for entry in entries if entry.signature_status == TimeEntry.SignatureStatus.SIGNED)
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
    tracked_fields = {"work_date", "family_name", "start_time", "end_time", "total_hours", "notes"}
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
        "nanny_name": timesheet.nanny.get_full_name() or timesheet.nanny.username,
        "week_start_date": timesheet.week_start_date.isoformat(),
        "week_end_date": timesheet.week_end_date.isoformat(),
        "total_hours": str(total_hours),
        "entries": [
            {
                "id": entry.id,
                "work_date": entry.work_date.isoformat(),
                "family_name": entry.family_name,
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


@transaction.atomic
def submit_timesheet(timesheet):
    entries = list(timesheet.entries.select_related("parent_signature").all())
    if not entries:
        raise ValidationError({"detail": "A timesheet must have at least one entry before submission."})
    if timesheet.is_submitted or timesheet.submission_id:
        raise ValidationError({"detail": "This timesheet has already been submitted."})

    total_hours = sum((entry.total_hours for entry in entries), Decimal("0.00"))
    has_unsigned_entries = any(entry.signature_status != TimeEntry.SignatureStatus.SIGNED for entry in entries)
    status = (
        WeeklyTimesheet.Status.SUBMITTED_WITH_UNSIGNED_ENTRIES
        if has_unsigned_entries
        else WeeklyTimesheet.Status.SUBMITTED_FULLY_SIGNED
    )
    timestamp = timezone.now()
    timesheet.status = status
    timesheet.submitted_at = timestamp
    pdf_bytes = generate_timesheet_pdf(timesheet)
    file_name = f"timesheet_{timesheet.id}_{timestamp:%Y%m%d%H%M%S}.pdf"
    snapshot = _build_submission_snapshot(timesheet, entries, total_hours)

    submission = TimesheetSubmission.objects.create(
        status=status,
        submitted_by=timesheet.nanny,
        total_hours=total_hours,
        snapshot=snapshot,
    )
    submission.pdf_file.save(file_name, ContentFile(pdf_bytes), save=True)

    timesheet.submission = submission
    timesheet.pdf_file.save(file_name, ContentFile(pdf_bytes), save=False)
    timesheet.save(update_fields=["submission", "submitted_at", "status", "pdf_file", "updated_at"])
    return timesheet
