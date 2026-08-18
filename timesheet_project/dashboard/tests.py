import shutil
from datetime import date, time, timedelta
from pathlib import Path

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from timesheets.models import TimeEntry, WeeklyTimesheet
from timesheets.services import calculate_total_hours, get_timesheet_week_range, submit_timesheet


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
        self.current_week_start, _ = get_timesheet_week_range(timezone.localdate())
        self.client.force_login(self.admin)

    def create_submitted_timesheet(self, nanny, week_start, requested_entries=0, force_late=False):
        timesheet = WeeklyTimesheet.objects.create(
            nanny=nanny,
            week_start_date=week_start,
            week_end_date=week_start + timedelta(days=6),
        )
        entry_count = max(1, requested_entries)
        for index in range(entry_count):
            TimeEntry.objects.create(
                timesheet=timesheet,
                work_date=week_start + timedelta(days=min(index, 6)),
                family_name=f"Smith {index + 1}",
                start_time=time(9, 0),
                end_time=time(17, 0),
                total_hours=calculate_total_hours(time(9, 0), time(17, 0)),
                family_requested_nanny=index < requested_entries,
            )
        return submit_timesheet(timesheet, force_late=force_late)

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

    def test_dashboard_defaults_to_current_week(self):
        current_timesheet = self.create_submitted_timesheet(self.active_nanny, self.current_week_start)
        previous_week_start = self.current_week_start - timedelta(days=7)
        previous_timesheet = self.create_submitted_timesheet(self.active_nanny, previous_week_start)

        response = self.client.get(reverse("dashboard-index"))

        self.assertContains(response, f"timesheet-modal-{current_timesheet.id}")
        self.assertNotContains(response, f"timesheet-modal-{previous_timesheet.id}")
        self.assertContains(response, f'value="{self.current_week_start.isoformat()}" selected', html=False)

    def test_dashboard_table_uses_modal_without_id_column(self):
        timesheet = self.create_submitted_timesheet(self.active_nanny, self.current_week_start)

        response = self.client.get(reverse("dashboard-index"))

        self.assertContains(response, "Active Nanny —")
        self.assertContains(response, f'data-target="timesheet-modal-{timesheet.id}"', html=False)
        self.assertContains(response, f'id="timesheet-modal-{timesheet.id}"', html=False)
        self.assertContains(response, "View PDF")
        self.assertNotContains(response, "<th>ID</th>", html=False)

    def test_dashboard_shows_multiple_indicators_and_incentive_drilldown(self):
        timesheet = self.create_submitted_timesheet(
            self.active_nanny,
            self.current_week_start,
            requested_entries=5,
            force_late=True,
        )

        response = self.client.get(reverse("dashboard-index"))

        self.assertContains(response, f"timesheet-modal-{timesheet.id}")
        self.assertContains(response, "Unsigned entries")
        self.assertContains(response, "Late submission")
        self.assertContains(response, "Request incentive")
        self.assertContains(response, "Request Incentive Milestones")
        self.assertContains(response, "Earned on lifetime request #5")
        self.assertContains(response, "Smith 5")

    def test_dashboard_modal_shows_requested_markers_and_entry_notes(self):
        timesheet = WeeklyTimesheet.objects.create(
            nanny=self.active_nanny,
            week_start_date=self.current_week_start,
            week_end_date=self.current_week_start + timedelta(days=6),
        )
        TimeEntry.objects.create(
            timesheet=timesheet,
            work_date=self.current_week_start,
            family_name="Smith",
            start_time=time(9, 0),
            end_time=time(17, 0),
            total_hours=calculate_total_hours(time(9, 0), time(17, 0)),
            family_requested_nanny=True,
            notes="Parent asked for extra pickup notes.",
        )
        submit_timesheet(timesheet)

        response = self.client.get(reverse("dashboard-index"))

        self.assertContains(response, "Requested")
        self.assertContains(response, "Parent asked for extra pickup notes.")
        self.assertContains(response, "Admin Notes")
