import shutil
from datetime import date, time, timedelta
from pathlib import Path

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from timesheets.models import TimeEntry, WeeklyTimesheet
from timesheets.services import calculate_total_hours, submit_timesheet


TEST_MEDIA_ROOT = Path(settings.BASE_DIR) / "test_media_dashboard"


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class DashboardFilterTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        if TEST_MEDIA_ROOT.exists():
            shutil.rmtree(TEST_MEDIA_ROOT)

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin",
            password="StrongTestPass123!",
            role=User.Role.ADMIN,
            is_staff=True,
        )
        self.active_nanny = User.objects.create_user(
            username="active-nanny",
            password="StrongTestPass123!",
            role=User.Role.NANNY,
            first_name="Active",
            last_name="Nanny",
            is_active=True,
        )
        self.inactive_nanny = User.objects.create_user(
            username="inactive-nanny",
            password="StrongTestPass123!",
            role=User.Role.NANNY,
            first_name="Inactive",
            last_name="Nanny",
            is_active=False,
        )
        self.client.force_login(self.admin)

    def create_submitted_timesheet(self, nanny, week_start):
        timesheet = WeeklyTimesheet.objects.create(
            nanny=nanny,
            week_start_date=week_start,
            week_end_date=week_start + timedelta(days=6),
        )
        TimeEntry.objects.create(
            timesheet=timesheet,
            work_date=week_start,
            family_name="Smith",
            start_time=time(9, 0),
            end_time=time(17, 0),
            total_hours=calculate_total_hours(time(9, 0), time(17, 0)),
        )
        return submit_timesheet(timesheet)

    def test_dashboard_uses_dropdown_filters_without_nanny_id_search(self):
        self.create_submitted_timesheet(self.active_nanny, date(2026, 7, 11))

        response = self.client.get(reverse("dashboard-index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<select id="week_start" name="week_start">', html=False)
        self.assertContains(response, '<select id="nanny" name="nanny">', html=False)
        self.assertContains(response, '<select id="status" name="status">', html=False)
        self.assertNotContains(response, 'placeholder="Nanny ID"')

    def test_dashboard_nanny_dropdown_defaults_to_active_nannies(self):
        self.create_submitted_timesheet(self.active_nanny, date(2026, 7, 11))
        self.create_submitted_timesheet(self.inactive_nanny, date(2026, 7, 18))

        response = self.client.get(reverse("dashboard-index"))

        self.assertContains(response, "Active Nanny")
        self.assertNotContains(response, "Inactive Nanny (inactive)")

    def test_dashboard_can_show_inactive_nannies_in_dropdown(self):
        self.create_submitted_timesheet(self.inactive_nanny, date(2026, 7, 18))

        response = self.client.get(reverse("dashboard-index"), {"nanny_status": "inactive"})

        self.assertContains(response, "Inactive Nanny (inactive)")

    def test_dashboard_filters_by_selected_nanny_and_week_dropdown_value(self):
        selected_timesheet = self.create_submitted_timesheet(self.active_nanny, date(2026, 7, 11))
        self.create_submitted_timesheet(self.inactive_nanny, date(2026, 7, 18))

        response = self.client.get(
            reverse("dashboard-index"),
            {
                "week_start": selected_timesheet.week_start_date.isoformat(),
                "nanny": str(self.active_nanny.pk),
            },
        )

        self.assertContains(response, "Active Nanny")
        self.assertNotContains(response, "Inactive Nanny")
        self.assertContains(response, 'value="2026-07-11" selected', html=False)
