from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User


class NannyManagementAPIRegressionTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="api-nanny-admin",
            password="StrongTestPass123!",
            role=User.Role.ADMIN,
        )
        self.client.force_authenticate(user=self.admin)

    def test_nanny_api_excludes_superusers(self):
        developer = User.objects.create_superuser(
            username="developer-nanny-api",
            password="StrongTestPass123!",
            role=User.Role.NANNY,
        )
        nanny = User.objects.create_user(
            username="regular-nanny-api",
            password="StrongTestPass123!",
            role=User.Role.NANNY,
        )

        response = self.client.get(reverse("admin-nanny-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        usernames = {item["username"] for item in response.data}
        self.assertIn(nanny.username, usernames)
        self.assertNotIn(developer.username, usernames)

    def test_nanny_api_cannot_patch_superusers(self):
        developer = User.objects.create_superuser(
            username="developer-nanny-api-patch",
            password="StrongTestPass123!",
            role=User.Role.NANNY,
        )

        response = self.client.patch(
            reverse("admin-nanny-detail", args=[developer.id]),
            {"first_name": "Edited"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        developer.refresh_from_db()
        self.assertEqual(developer.first_name, "")
