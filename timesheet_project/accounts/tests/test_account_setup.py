from datetime import timedelta

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import AccountSetupToken, User
from accounts.services import create_account_setup_token, hash_setup_token


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    ACCOUNT_SETUP_BASE_URL="https://example.com",
)
class AccountSetupFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="admin",
            password="StrongTestPass123!",
            role=User.Role.ADMIN,
        )
        self.client.force_authenticate(user=self.admin)

    def test_admin_created_nanny_has_unusable_password_and_receives_setup_email(self):
        response = self.client.post(
            reverse("admin-nanny-list"),
            {
                "first_name": "New",
                "last_name": "Nanny",
                "email": "new.nanny@example.com",
                "phone": "555-0101",
                "is_active": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="new.nanny@example.com")
        self.assertTrue(user.username.startswith("pending-"))
        self.assertFalse(user.has_usable_password())
        self.assertFalse(user.force_password_change)
        self.assertEqual(user.role, User.Role.NANNY)
        self.assertEqual(AccountSetupToken.objects.filter(user=user, used_at__isnull=True).count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Set up your Timesheet account", mail.outbox[0].subject)
        self.assertIn("https://example.com/api/auth/account-setup/validate/?token=", mail.outbox[0].body)

    def test_admin_payload_cannot_set_password_or_force_reset(self):
        response = self.client.post(
            reverse("admin-dashboard-user-list"),
            {
                "first_name": "Office",
                "last_name": "User",
                "email": "office@example.com",
                "phone": "555-0102",
                "role": User.Role.OFFICE,
                "is_active": True,
                "password": "AdminChosenPassword123!",
                "force_password_change": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="office@example.com")
        self.assertFalse(user.has_usable_password())
        self.assertFalse(user.check_password("AdminChosenPassword123!"))
        self.assertFalse(user.force_password_change)

    def test_setup_request_uses_generic_response_and_sends_email_for_pending_user(self):
        user = User.objects.create_user(
            username="pending-user",
            first_name="Pending",
            last_name="User",
            email="pending@example.com",
            phone="555-0103",
            role=User.Role.NANNY,
        )
        user.set_unusable_password()
        user.save(update_fields=["password"])
        self.client.force_authenticate(user=None)

        response = self.client.post(
            reverse("account-setup-request"),
            {"identifier": "pending@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"],
            "If an account is eligible for setup, instructions have been sent.",
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(AccountSetupToken.objects.filter(user=user, used_at__isnull=True).count(), 1)

    def test_setup_request_does_not_reveal_missing_account(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(
            reverse("account-setup-request"),
            {"identifier": "missing@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"],
            "If an account is eligible for setup, instructions have been sent.",
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_user_can_complete_setup_with_valid_token(self):
        user = User.objects.create_user(
            username="pending-user",
            first_name="Pending",
            last_name="User",
            email="pending@example.com",
            phone="555-0104",
            role=User.Role.NANNY,
        )
        user.set_unusable_password()
        user.save(update_fields=["password"])
        raw_token, setup_token = create_account_setup_token(user)
        self.client.force_authenticate(user=None)

        response = self.client.post(
            reverse("account-setup-complete"),
            {
                "token": raw_token,
                "username": "real-nanny",
                "password": "StrongTestPass123!",
                "confirm_password": "StrongTestPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        setup_token.refresh_from_db()
        self.assertEqual(user.username, "real-nanny")
        self.assertTrue(user.check_password("StrongTestPass123!"))
        self.assertFalse(user.force_password_change)
        self.assertIsNotNone(setup_token.used_at)

    def test_expired_setup_token_cannot_be_used(self):
        user = User.objects.create_user(
            username="pending-user",
            email="pending@example.com",
            phone="555-0105",
            role=User.Role.NANNY,
        )
        user.set_unusable_password()
        user.save(update_fields=["password"])
        raw_token = "expired-token"
        AccountSetupToken.objects.create(
            user=user,
            token_hash=hash_setup_token(raw_token),
            expires_at=timezone.now() - timedelta(days=1),
        )
        self.client.force_authenticate(user=None)

        response = self.client.post(
            reverse("account-setup-complete"),
            {
                "token": raw_token,
                "username": "real-nanny",
                "password": "StrongTestPass123!",
                "confirm_password": "StrongTestPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        user.refresh_from_db()
        self.assertFalse(user.has_usable_password())
