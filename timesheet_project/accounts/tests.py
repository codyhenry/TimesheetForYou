from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User


class RoleAccessModelTests(TestCase):
    def test_office_admin_and_staff_can_access_dashboard(self):
        office = User.objects.create_user(username="office", role=User.Role.OFFICE)
        admin = User.objects.create_user(username="admin", role=User.Role.ADMIN)
        staff = User.objects.create_user(username="staff", is_staff=True)

        self.assertTrue(office.can_access_dashboard)
        self.assertTrue(admin.can_access_dashboard)
        self.assertTrue(staff.can_access_dashboard)
        self.assertFalse(office.can_access_django_admin)
        self.assertFalse(admin.can_access_django_admin)
        self.assertTrue(staff.can_access_django_admin)

    def test_nanny_and_inactive_users_cannot_access_dashboard(self):
        nanny = User.objects.create_user(username="nanny", role=User.Role.NANNY)
        inactive_admin = User.objects.create_user(
            username="inactive-admin",
            role=User.Role.ADMIN,
            is_active=False,
        )

        self.assertFalse(nanny.can_access_dashboard)
        self.assertFalse(inactive_admin.can_access_dashboard)


class DashboardBrowserAccessTests(TestCase):
    def test_office_user_can_open_dashboard_page(self):
        office = User.objects.create_user(
            username="office",
            password="StrongTestPass123!",
            role=User.Role.OFFICE,
        )
        self.client.force_login(office)

        response = self.client.get(reverse("dashboard-index"))

        self.assertEqual(response.status_code, 200)

    def test_nanny_user_is_redirected_from_dashboard_page(self):
        nanny = User.objects.create_user(
            username="nanny",
            password="StrongTestPass123!",
            role=User.Role.NANNY,
        )
        self.client.force_login(nanny)

        response = self.client.get(reverse("dashboard-index"))

        self.assertEqual(response.status_code, 302)


class RoleAccessAPITests(APITestCase):
    def setUp(self):
        self.nanny = User.objects.create_user(
            username="nanny",
            password="StrongTestPass123!",
            role=User.Role.NANNY,
        )
        self.office = User.objects.create_user(
            username="office",
            password="StrongTestPass123!",
            role=User.Role.OFFICE,
        )
        self.admin = User.objects.create_user(
            username="admin",
            password="StrongTestPass123!",
            role=User.Role.ADMIN,
        )

    def test_current_user_exposes_access_flags(self):
        self.client.force_authenticate(user=self.office)

        response = self.client.get(reverse("current-user"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["role"], User.Role.OFFICE)
        self.assertTrue(response.data["can_access_dashboard"])
        self.assertFalse(response.data["can_access_django_admin"])
        self.assertFalse(response.data["force_password_change"])

    def test_office_user_can_access_admin_timesheet_api(self):
        self.client.force_authenticate(user=self.office)

        response = self.client.get(reverse("admin-timesheet-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_nanny_cannot_access_admin_timesheet_api(self):
        self.client.force_authenticate(user=self.nanny)

        response = self.client.get(reverse("admin-timesheet-list"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_office_user_cannot_manage_dashboard_users(self):
        self.client.force_authenticate(user=self.office)

        response = self.client.get(reverse("admin-dashboard-user-list"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_office_user_with_forced_password_change(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            reverse("admin-dashboard-user-list"),
            {
                "username": "new-office",
                "password": "TemporaryPass123!",
                "first_name": "New",
                "last_name": "Office",
                "role": User.Role.OFFICE,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="new-office")
        self.assertEqual(user.role, User.Role.OFFICE)
        self.assertFalse(user.is_staff)
        self.assertTrue(user.force_password_change)
        self.assertTrue(user.check_password("TemporaryPass123!"))

    def test_admin_cannot_create_dashboard_user_with_nanny_role(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            reverse("admin-dashboard-user-list"),
            {
                "username": "bad-dashboard-user",
                "password": "TemporaryPass123!",
                "role": User.Role.NANNY,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("role", response.data)

    def test_admin_can_flag_nanny_for_password_setup(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            reverse("admin-nanny-list"),
            {
                "username": "new-nanny",
                "password": "TemporaryPass123!",
                "first_name": "New",
                "last_name": "Nanny",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="new-nanny")
        self.assertEqual(user.role, User.Role.NANNY)
        self.assertTrue(user.force_password_change)
        self.assertTrue(user.check_password("TemporaryPass123!"))
