from datetime import time

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from timesheets.models import TimeEntry, WeeklyTimesheet
from timesheets.services import calculate_total_hours, get_timesheet_week_range, submit_timesheet


class DashboardUserManagementPasswordRegressionTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin-regression",
            password="StrongTestPass123!",
            role=User.Role.ADMIN,
        )
        self.client.force_login(self.admin)

    def test_update_without_temporary_password_preserves_existing_password_hash(self):
        nanny = User.objects.create_user(
            username="nanny-password-preserved",
            password="ExistingStrongPass123!",
            role=User.Role.NANNY,
            first_name="Original",
            last_name="Nanny",
            force_password_change=False,
        )
        original_password_hash = nanny.password

        response = self.client.post(
            reverse("dashboard-users"),
            {
                "action": "update",
                "user_id": str(nanny.id),
                f"user-{nanny.id}-first_name": "Updated",
                f"user-{nanny.id}-last_name": "Nanny",
                f"user-{nanny.id}-email": "updated@example.com",
                f"user-{nanny.id}-phone": "555-0104",
                f"user-{nanny.id}-role": User.Role.NANNY,
                f"user-{nanny.id}-is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        nanny.refresh_from_db()
        self.assertEqual(nanny.password, original_password_hash)
        self.assertTrue(nanny.check_password("ExistingStrongPass123!"))
        self.assertFalse(nanny.force_password_change)
        self.assertEqual(nanny.first_name, "Updated")

    def test_update_with_temporary_password_resets_password_and_forces_setup(self):
        nanny = User.objects.create_user(
            username="nanny-password-reset",
            password="ExistingStrongPass123!",
            role=User.Role.NANNY,
            force_password_change=False,
        )

        response = self.client.post(
            reverse("dashboard-users"),
            {
                "action": "update",
                "user_id": str(nanny.id),
                f"user-{nanny.id}-first_name": "Reset",
                f"user-{nanny.id}-last_name": "Nanny",
                f"user-{nanny.id}-email": "reset@example.com",
                f"user-{nanny.id}-role": User.Role.NANNY,
                f"user-{nanny.id}-is_active": "on",
                f"user-{nanny.id}-temporary_password": "NewStrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 302)
        nanny.refresh_from_db()
        self.assertTrue(nanny.check_password("NewStrongPass123!"))
        self.assertTrue(nanny.force_password_change)


class DashboardEntryNotesRegressionTests(TestCase):
    def test_empty_entry_notes_render_visible_placeholder(self):
        admin = User.objects.create_user(
            username="admin-notes-placeholder",
            password="StrongTestPass123!",
            role=User.Role.ADMIN,
        )
        nanny = User.objects.create_user(
            username="nanny-notes-placeholder",
            password="StrongTestPass123!",
            role=User.Role.NANNY,
            first_name="Notes",
            last_name="Nanny",
        )
        week_start, _ = get_timesheet_week_range(timezone.localdate())
        timesheet = WeeklyTimesheet.objects.create(
            nanny=nanny,
            week_start_date=week_start,
            week_end_date=week_start + timezone.timedelta(days=6),
        )
        TimeEntry.objects.create(
            timesheet=timesheet,
            work_date=week_start,
            family_name="Smith",
            start_time=time(9, 0),
            end_time=time(17, 0),
            total_hours=calculate_total_hours(time(9, 0), time(17, 0)),
            notes="",
        )
        submit_timesheet(timesheet)
        self.client.force_login(admin)

        response = self.client.get(reverse("dashboard-index"))

        self.assertContains(response, '<td class="notes-cell">—</td>', html=False)
