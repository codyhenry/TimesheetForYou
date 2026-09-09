import logging

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse

from .models import WeeklyTimesheet

logger = logging.getLogger(__name__)


class NotificationConfigurationError(RuntimeError):
    pass


def sns_notifications_enabled():
    return bool(getattr(settings, "USE_SNS", False))


def _build_sns_client():
    region_name = getattr(settings, "AWS_SNS_REGION_NAME", "") or getattr(settings, "AWS_REGION", "")
    if not region_name:
        raise NotificationConfigurationError(
            "AWS_SNS_REGION_NAME or AWS_REGION must be set when USE_SNS=True."
        )

    import boto3

    return boto3.client("sns", region_name=region_name)


def _not_sent_result(phone_number, reason):
    return {
        "sent": False,
        "phone_number": phone_number,
        "message_id": "",
        "reason": reason,
    }


def send_sms_notification(phone_number, message, sns_client=None):
    """Send an SMS message through AWS SNS.

    When USE_SNS is false this is a safe no-op so reminder workflows can be
    tested or dry-run without sending external messages. Publish/configuration
    failures are returned as non-sent results so scheduled reminder runs can
    continue processing remaining recipients.
    """
    normalized_phone_number = str(phone_number or "").strip()
    if not normalized_phone_number:
        raise ValueError("phone_number is required")
    if not message:
        raise ValueError("message is required")

    if not sns_notifications_enabled():
        return _not_sent_result(
            normalized_phone_number,
            "SNS notifications are disabled.",
        )

    try:
        client = sns_client or _build_sns_client()
        publish_kwargs = {
            "PhoneNumber": normalized_phone_number,
            "Message": message,
        }
        sender_id = getattr(settings, "SNS_SENDER_ID", "")
        if sender_id:
            publish_kwargs["MessageAttributes"] = {
                "AWS.SNS.SMS.SenderID": {
                    "DataType": "String",
                    "StringValue": sender_id,
                }
            }

        response = client.publish(**publish_kwargs)
    except Exception as exc:  # pragma: no cover - exact SNS exception types vary by botocore version.
        return _not_sent_result(
            normalized_phone_number,
            f"SNS publish failed: {exc}",
        )

    return {
        "sent": True,
        "phone_number": normalized_phone_number,
        "message_id": response.get("MessageId", ""),
        "reason": "",
    }


def _format_short_date(value):
    return f"{value.month}.{value.day}.{value.year % 100:02d}"


def _format_week_range(timesheet):
    return f"{_format_short_date(timesheet.week_start_date)}-{_format_short_date(timesheet.week_end_date)}"


def _build_dashboard_url(timesheet):
    base_url = settings.SITE_BASE_URL.rstrip("/")
    return f"{base_url}{reverse('dashboard-detail', args=[timesheet.id])}"


def send_timesheet_submission_admin_email(timesheet_id):
    """Notify the configured admin email after a timesheet is submitted.

    Returns True when an email is sent, False when notifications are disabled or
    delivery fails. Delivery errors are logged but do not undo the submission.
    """
    recipient = getattr(settings, "ADMIN_NOTIFICATION_EMAIL", "")
    if not recipient:
        return False

    timesheet = (
        WeeklyTimesheet.objects.select_related("nanny", "submission")
        .filter(pk=timesheet_id)
        .first()
    )
    if timesheet is None or timesheet.submission is None:
        return False

    nanny_name = timesheet.nanny.get_full_name() or timesheet.nanny.username
    week_range = _format_week_range(timesheet)
    dashboard_url = _build_dashboard_url(timesheet)
    late_status = "Yes" if timesheet.is_late_submission else "No"

    subject = f"Timesheet submitted: {nanny_name}, {week_range}"
    message = "\n".join(
        [
            f"{nanny_name} submitted a timesheet for {week_range}.",
            "",
            f"Status: {timesheet.get_status_display()}",
            f"Total hours: {timesheet.submission.total_hours}",
            f"Late: {late_status}",
            "",
            f"View it in the dashboard: {dashboard_url}",
        ]
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
    except Exception:
        logger.exception("Failed to send timesheet submission notification for timesheet %s", timesheet_id)
        return False

    return True
