from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import AccountSetupToken, User
from accounts.services import create_account_setup_token, send_account_setup_email


@override_settings(
    ACCOUNT_SETUP_BASE_URL="https://timesheets.example.com",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class AccountSetupWebFlowTests(TestCase):
    def create_pending_user(self):
        user = User.objects.create_user(
            username="pending-user",
            first_name="Nina",
            last_name="Nanny",
            email="nina@example.com",
            phone="555-0101",
            role=User.Role.NANNY,
        )
        user.set_unusable_password()
        user.save(update_fields=["password"])
        return user

    def test_setup_email_points_to_public_setup_page(self):
        user = self.create_pending_user()

        send_account_setup_email(user)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("https://timesheets.example.com/account-setup/?token=", mail.outbox[0].body)
        self.assertNotIn("/api/auth/account-setup/validate/", mail.outbox[0].body)

    def test_setup_page_renders_completion_form_for_valid_token(self):
        user = self.create_pending_user()
        raw_token, _ = create_account_setup_token(user)

        response = self.client.get(reverse("account-setup-web"), {"token": raw_token})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Set up your account")
        self.assertContains(response, "Finish setup")
        self.assertContains(response, "Nina Nanny")

    def test_setup_page_completes_username_and_password(self):
        user = self.create_pending_user()
        raw_token, setup_token = create_account_setup_token(user)

        response = self.client.post(
            reverse("account-setup-web"),
            {
                "action": "complete",
                "token": raw_token,
                "username": "nina-nanny",
                "password": "StrongTestPass123!",
                "confirm_password": "StrongTestPass123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Account setup complete")
        user.refresh_from_db()
        setup_token.refresh_from_db()
        self.assertEqual(user.username, "nina-nanny")
        self.assertTrue(user.check_password("StrongTestPass123!"))
        self.assertIsNotNone(setup_token.used_at)

    def test_setup_page_can_request_new_setup_email_generically(self):
        self.create_pending_user()

        response = self.client.post(
            reverse("account-setup-web"),
            {
                "action": "request",
                "identifier": "nina@example.com",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "If an account is eligible for setup, instructions have been sent.")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(AccountSetupToken.objects.filter(used_at__isnull=True).count(), 1)

    def test_setup_page_rejects_invalid_or_expired_token(self):
        response = self.client.get(reverse("account-setup-web"), {"token": "missing"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Setup link expired")
        self.assertContains(response, "Request setup instructions")
