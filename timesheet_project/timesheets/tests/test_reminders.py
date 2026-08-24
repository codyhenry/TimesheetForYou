from datetime import date, time
from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings

from accounts.models import User
from timesheets.models import TimeEntry, TimesheetWeekLock, WeeklyTimesheet
from timesheets.notifications import send_sms_notification
from timesheets.reminders import (
    get_timesheet_reminder_recipients,
    send_due_timesheet_reminders,
)
from timesheets.services import calculate_total_hours, submit_timesheet


class FakeSnsClient:
    def __init__(self):
        self.publish_calls = []

    def publish(self, **kwargs):
        self.publish_calls.append(kwargs)
        return {"MessageId": f"message-{len(self.publish_calls)}"}


class TimesheetReminderTests(TestCase):
    def setUp(self):
        self.week_start = date(2026, 7, 11)
        self.week_end = date(2026, 7, 17)
        self.nanny = User.objects.create_user(
            username="nanny1",
            password="StrongTestPass123!",
            role=User.Role.NANNY,
            first_name="Nina",
            last_name="Nanny",
            phone="+15555550100",
        )

    def create_timesheet(self, nanny=None, status=WeeklyTimesheet.Status.DRAFT):
        return WeeklyTimesheet.objects.create(
            nanny=nanny or self.nanny,
            week_start_date=self.week_start,
            week_end_date=self.week_end,
            status=status,
        )

    def create_entry(self, timesheet):
        return TimeEntry.objects.create(
            timesheet=timesheet,
            work_date=self.week_start,
            family_name="Smith",
            start_time=time(9, 0),
            end_time=time(17, 0),
            total_hours=calculate_total_hours(time(9, 0), time(17, 0)),
        )

    def test_recipients_include_active_nannies_with_missing_or_unsubmitted_timesheets(self):
        draft_timesheet = self.create_timesheet()
        missing_timesheet_nanny = User.objects.create_user(
            username="nanny2",
            password="StrongTestPass123!",
            role=User.Role.NANNY,
            phone="+15555550101",
        )

        recipients = get_timesheet_reminder_recipients(week_start_date=self.week_start)

        recipient_ids = {recipient.nanny_id for recipient in recipients}
        self.assertEqual(recipient_ids, {self.nanny.id, missing_timesheet_nanny.id})
        statuses = {recipient.nanny_id: recipient.timesheet_status for recipient in recipients}
        self.assertEqual(statuses[self.nanny.id], draft_timesheet.status)
        self.assertEqual(statuses[missing_timesheet_nanny.id], "missing")

    def test_recipients_skip_submitted_inactive_no_phone_non_nanny_and_locked_weeks(self):
        submitted_nanny = User.objects.create_user(
            username="submitted",
            password="StrongTestPass123!",
            role=User.Role.NANNY,
            phone="+15555550102",
        )
        submitted_timesheet = self.create_timesheet(nanny=submitted_nanny)
        self.create_entry(submitted_timesheet)
        submit_timesheet(submitted_timesheet)
        User.objects.create_user(
            username="inactive",
            password="StrongTestPass123!",
            role=User.Role.NANNY,
            phone="+15555550103",
            is_active=False,
        )
        User.objects.create_user(
            username="no_phone",
            password="StrongTestPass123!",
            role=User.Role.NANNY,
        )
        User.objects.create_user(
            username="office",
            password="StrongTestPass123!",
            role=User.Role.OFFICE,
            phone="+15555550104",
        )

        recipients = get_timesheet_reminder_recipients(week_start_date=self.week_start)

        self.assertEqual([recipient.nanny_id for recipient in recipients], [self.nanny.id])

        TimesheetWeekLock.objects.create(
            week_start_date=self.week_start,
            week_end_date=self.week_end,
        )
        self.assertEqual(get_timesheet_reminder_recipients(week_start_date=self.week_start), [])

    def test_disabled_sns_is_safe_noop(self):
        result = send_sms_notification("+15555550100", "Reminder")

        self.assertFalse(result["sent"])
        self.assertEqual(result["reason"], "SNS notifications are disabled.")

    @override_settings(USE_SNS=True, AWS_SNS_REGION_NAME="us-east-1", SNS_SENDER_ID="Timesheet")
    def test_send_due_timesheet_reminders_publishes_to_sns_client(self):
        sns_client = FakeSnsClient()

        summary = send_due_timesheet_reminders(
            week_start_date=self.week_start,
            sns_client=sns_client,
        )

        self.assertEqual(summary["recipient_count"], 1)
        self.assertEqual(summary["sent_count"], 1)
        self.assertEqual(len(sns_client.publish_calls), 1)
        publish_call = sns_client.publish_calls[0]
        self.assertEqual(publish_call["PhoneNumber"], "+15555550100")
        self.assertIn("7/11/26-7/17/26", publish_call["Message"])
        self.assertEqual(
            publish_call["MessageAttributes"]["AWS.SNS.SMS.SenderID"]["StringValue"],
            "Timesheet",
        )

    def test_send_due_timesheet_reminders_dry_run_does_not_publish(self):
        sns_client = FakeSnsClient()

        summary = send_due_timesheet_reminders(
            week_start_date=self.week_start,
            dry_run=True,
            sns_client=sns_client,
        )

        self.assertEqual(summary["recipient_count"], 1)
        self.assertEqual(summary["sent_count"], 0)
        self.assertEqual(sns_client.publish_calls, [])
        self.assertEqual(summary["results"][0]["reason"], "Dry run; notification was not sent.")

    def test_management_command_supports_dry_run_for_specific_week(self):
        stdout = StringIO()

        call_command(
            "send_timesheet_reminders",
            "--week-start",
            str(self.week_start),
            "--dry-run",
            stdout=stdout,
        )

        output = stdout.getvalue()
        self.assertIn("Dry run reminders for 2026-07-11 - 2026-07-17", output)
        self.assertIn("1 eligible", output)
        self.assertIn("Dry run; notification was not sent", output)
