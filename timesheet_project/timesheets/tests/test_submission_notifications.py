from datetime import date, datetime, time
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import User
from timesheets.models import TimeEntry, WeeklyTimesheet
from timesheets.notifications import send_timesheet_submission_admin_email
from timesheets.services import calculate_total_hours, submit_timesheet


@override_settings(
    ADMIN_NOTIFICATION_EMAIL="admin@example.com",
    DEFAULT_FROM_EMAIL="no-reply@example.com",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    MEDIA_ROOT="test_media_submission_notifications",
    SITE_BASE_URL="https://timesheets.example.com",
)
class TimesheetSubmissionNotificationTests(TestCase):
    def setUp(self):
        self.nanny = User.objects.create_user(
            username="nanny1",
            password="StrongTestPass123!",
            role=User.Role.NANNY,
            first_name="Nina",
            last_name="Nanny",
        )
        self.timesheet = WeeklyTimesheet.objects.create(
            nanny=self.nanny,
            week_start_date=date(2026, 7, 11),
            week_end_date=date(2026, 7, 17),
        )
        TimeEntry.objects.create(
            timesheet=self.timesheet,
            work_date=date(2026, 7, 11),
            family_name="Smith",
            start_time=time(9, 0),
            end_time=time(17, 0),
            total_hours=calculate_total_hours(time(9, 0), time(17, 0)),
        )

    def test_submission_sends_admin_email_after_commit(self):
        submitted_before_deadline = timezone.make_aware(datetime(2026, 7, 18, 11, 0))
        with patch("timesheets.services.timezone.now", return_value=submitted_before_deadline):
            with self.captureOnCommitCallbacks(execute=True):
                submit_timesheet(self.timesheet)

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ["admin@example.com"])
        self.assertEqual(message.from_email, "no-reply@example.com")
        self.assertIn("Timesheet submitted: Nina Nanny, 7.11.26-7.17.26", message.subject)
        self.assertIn("Nina Nanny submitted a timesheet for 7.11.26-7.17.26.", message.body)
        self.assertIn("Status: Submitted With Unsigned Entries", message.body)
        self.assertIn("Total hours: 8.00", message.body)
        self.assertIn("Late: No", message.body)
        self.assertIn(
            f"https://timesheets.example.com/dashboard/timesheets/{self.timesheet.id}/",
            message.body,
        )

    @override_settings(ADMIN_NOTIFICATION_EMAIL="")
    def test_submission_email_is_disabled_without_admin_recipient(self):
        with self.captureOnCommitCallbacks(execute=True):
            submit_timesheet(self.timesheet)

        self.assertEqual(len(mail.outbox), 0)

    def test_submission_email_delivery_failure_does_not_break_submission(self):
        with patch("timesheets.notifications.send_mail", side_effect=RuntimeError("SMTP down")):
            with self.captureOnCommitCallbacks(execute=True):
                submit_timesheet(self.timesheet)

        self.timesheet.refresh_from_db()
        self.assertIsNotNone(self.timesheet.submission)
        self.assertTrue(self.timesheet.is_submitted)

    def test_notification_helper_returns_false_for_missing_timesheet(self):
        self.assertFalse(send_timesheet_submission_admin_email(999999))
