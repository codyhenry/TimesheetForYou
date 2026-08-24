from dataclasses import dataclass
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import TimesheetWeekLock, WeeklyTimesheet
from .notifications import send_sms_notification
from .services import SUBMITTED_STATUSES, get_timesheet_submission_deadline, get_timesheet_week_range


@dataclass(frozen=True)
class TimesheetReminderRecipient:
    nanny_id: int
    nanny_name: str
    phone_number: str
    week_start_date: date
    week_end_date: date
    timesheet_id: int | None
    timesheet_status: str


def get_latest_due_timesheet_week(reference_time=None):
    """Return the latest Saturday-Friday week whose submission deadline has passed."""
    current_time = reference_time or timezone.now()
    local_date = timezone.localdate(current_time)
    week_start, week_end = get_timesheet_week_range(local_date)

    while get_timesheet_submission_deadline(week_end) > current_time:
        week_start -= timedelta(days=7)
        week_end -= timedelta(days=7)

    return week_start, week_end


def get_timesheet_reminder_recipients(week_start_date=None, reference_time=None):
    """Find active nannies who still need to submit for the selected due week.

    A nanny is eligible when they have a usable phone number, the week is not
    locked, and they do not have a submitted timesheet for the week. This
    includes both draft/in-progress timesheets and nannies who never opened that
    week's sheet.
    """
    if week_start_date is None:
        week_start, week_end = get_latest_due_timesheet_week(reference_time=reference_time)
    else:
        week_start, week_end = get_timesheet_week_range(week_start_date)

    if TimesheetWeekLock.objects.filter(week_start_date=week_start).exists():
        return []

    timesheets = {
        timesheet.nanny_id: timesheet
        for timesheet in WeeklyTimesheet.objects.filter(week_start_date=week_start)
    }
    submitted_nanny_ids = {
        timesheet.nanny_id
        for timesheet in timesheets.values()
        if timesheet.status in SUBMITTED_STATUSES
    }

    User = get_user_model()
    nannies = (
        User.objects.filter(is_active=True, role=User.Role.NANNY)
        .exclude(phone="")
        .exclude(id__in=submitted_nanny_ids)
        .order_by("last_name", "first_name", "username", "id")
    )

    recipients = []
    for nanny in nannies:
        phone_number = str(nanny.phone or "").strip()
        if not phone_number:
            continue

        timesheet = timesheets.get(nanny.id)
        recipients.append(
            TimesheetReminderRecipient(
                nanny_id=nanny.id,
                nanny_name=nanny.get_full_name() or nanny.username,
                phone_number=phone_number,
                week_start_date=week_start,
                week_end_date=week_end,
                timesheet_id=timesheet.id if timesheet else None,
                timesheet_status=timesheet.status if timesheet else "missing",
            )
        )
    return recipients


def format_timesheet_reminder_message(recipient):
    week_range = (
        f"{recipient.week_start_date.month}/{recipient.week_start_date.day}/"
        f"{recipient.week_start_date.year % 100:02d}-"
        f"{recipient.week_end_date.month}/{recipient.week_end_date.day}/"
        f"{recipient.week_end_date.year % 100:02d}"
    )
    return (
        f"TimesheetForYou reminder: your timesheet for {week_range} is due. "
        "Please submit it as soon as you can."
    )


def send_due_timesheet_reminders(
    week_start_date=None,
    reference_time=None,
    dry_run=False,
    sns_client=None,
):
    recipients = get_timesheet_reminder_recipients(
        week_start_date=week_start_date,
        reference_time=reference_time,
    )
    results = []

    for recipient in recipients:
        message = format_timesheet_reminder_message(recipient)
        if dry_run:
            notification_result = {
                "sent": False,
                "phone_number": recipient.phone_number,
                "message_id": "",
                "reason": "Dry run; notification was not sent.",
            }
        else:
            notification_result = send_sms_notification(
                recipient.phone_number,
                message,
                sns_client=sns_client,
            )

        results.append(
            {
                "nanny_id": recipient.nanny_id,
                "nanny_name": recipient.nanny_name,
                "timesheet_id": recipient.timesheet_id,
                "timesheet_status": recipient.timesheet_status,
                "message": message,
                **notification_result,
            }
        )

    sent_count = sum(1 for result in results if result["sent"])
    week_start = recipients[0].week_start_date if recipients else None
    week_end = recipients[0].week_end_date if recipients else None
    if week_start is None:
        if week_start_date is None:
            week_start, week_end = get_latest_due_timesheet_week(reference_time=reference_time)
        else:
            week_start, week_end = get_timesheet_week_range(week_start_date)

    return {
        "week_start_date": week_start,
        "week_end_date": week_end,
        "recipient_count": len(results),
        "sent_count": sent_count,
        "results": results,
    }
