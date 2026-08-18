import shutil
from datetime import time, timedelta
from pathlib import Path

from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from timesheets.models import TimeEntry, TimesheetWeekLock, WeeklyTimesheet
from timesheets.services import calculate_total_hours, get_timesheet_week_range, submit_timesheet


TEST_MEDIA_ROOT = Path(settings.BASE_DIR) / "test_media_admin_request_inputs"


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class AdminRequestInputTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        if TEST_MEDIA_ROOT.exists():
            shutil.rmtree(TEST_MEDIA_ROOT)

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin-inputs",
            password="StrongTestPass123!",
            role=User.Role.ADMIN,
            is_staff=True,
        )
        self.nanny = User.objects.create_user(
            username="nanny-inputs",
            password="StrongTestPass123!",
            role=User.Role.NANNY,
            first_name="Nina",
            last_name="Nanny",
        )
        self.week_start, self.week_end = get_timesheet_week_range(timezone.localdate())
        self.client.force_authenticate(user=self.admin)

    def create_submitted_timesheet(self):
        timesheet = WeeklyTimesheet.objects.create(
            nanny=self.nanny,
            week_start_date=self.week_start,
            week_end_date=self.week_end,
        )
        TimeEntry.objects.create(
            timesheet=timesheet,
            work_date=self.week_start,
            family_name="Smith",
            start_time=time(9, 0),
            end_time=time(17, 0),
            total_hours=calculate_total_hours(time(9, 0), time(17, 0)),
        )
        return submit_timesheet(timesheet)

    def test_admin_override_submit_defaults_blank_late_note(self):
        timesheet = self.create_submitted_timesheet()

        response = self.client.post(
            reverse("admin-timesheet-override-submit", args=[timesheet.pk]),
            {"late_submission_note": "   "},
            format="json",
        )
        timesheet.refresh_from_db()
        assert timesheet.submission is not None

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(timesheet.late_submission_note, "Admin override submission.")
        self.assertEqual(
            timesheet.submission.late_submission_note,
            "Admin override submission.",
        )

    def test_admin_override_submit_casts_non_string_late_note(self):
        timesheet = self.create_submitted_timesheet()

        response = self.client.post(
            reverse("admin-timesheet-override-submit", args=[timesheet.pk]),
            {"late_submission_note": ["manual", "override"]},
            format="json",
        )
        timesheet.refresh_from_db()
        assert timesheet.submission is not None

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(timesheet.late_submission_note, "['manual', 'override']")
        self.assertEqual(timesheet.submission.late_submission_note, "['manual', 'override']")

    def test_lock_week_casts_and_strips_note(self):
        future_week_start = self.week_start + timedelta(days=7)

        response = self.client.post(
            reverse("admin-timesheet-lock-week"),
            {
                "week_start_date": future_week_start.isoformat(),
                "note": 12345,
            },
            format="json",
        )
        week_lock = TimesheetWeekLock.objects.get(week_start_date=future_week_start)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(week_lock.note, "12345")

    def test_lock_week_normalizes_blank_note_to_empty_string(self):
        future_week_start = self.week_start + timedelta(days=14)

        response = self.client.post(
            reverse("admin-timesheet-lock-week"),
            {
                "week_start_date": future_week_start.isoformat(),
                "note": "   ",
            },
            format="json",
        )
        week_lock = TimesheetWeekLock.objects.get(week_start_date=future_week_start)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(week_lock.note, "")
