from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User


class DashboardUserManagementAPIRegressionTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="api-admin",
            password="StrongTestPass123!",
            role=User.Role.ADMIN,
        )
        self.client.force_authenticate(user=self.admin)

    def test_dashboard_user_api_excludes_superusers(self):
        developer = User.objects.create_superuser(
            username="developer-api",
            password="StrongTestPass123!",
            role=User.Role.ADMIN,
        )
        office = User.objects.create_user(
            username="office-api",
            password="StrongTestPass123!",
            role=User.Role.OFFICE,
        )

        response = self.client.get(reverse("admin-dashboard-user-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        usernames = {item["username"] for item in response.data}
        self.assertIn(office.username, usernames)
        self.assertNotIn(developer.username, usernames)

    def test_dashboard_user_api_cannot_patch_superusers(self):
        developer = User.objects.create_superuser(
            username="developer-api-patch",
            password="StrongTestPass123!",
            role=User.Role.ADMIN,
        )

        response = self.client.patch(
            reverse("admin-dashboard-user-detail", args=[developer.id]),
            {"first_name": "Edited"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        developer.refresh_from_db()
        self.assertEqual(developer.first_name, "")
