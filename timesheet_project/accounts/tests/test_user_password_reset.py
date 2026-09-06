import re

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    SITE_BASE_URL="https://timesheets.example.com",
)
class UserPasswordResetFlowTests(TestCase):
    def test_request_uses_generic_response_for_missing_email(self):
        response = self.client.post(
            reverse("password-reset-request-web"),
            {"email": "missing@example.com"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "If an account exists for that email, password reset instructions have been sent.")
        self.assertEqual(len(mail.outbox), 0)

    def test_request_sends_reset_email_for_active_user_with_password(self):
        User.objects.create_user(
            username="nanny1",
            password="OldStrongPass123!",
            email="nanny@example.com",
            role=User.Role.NANNY,
            first_name="Nina",
        )

        response = self.client.post(
            reverse("password-reset-request-web"),
            {"email": "nanny@example.com"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Reset your Timesheet password", mail.outbox[0].subject)
        self.assertIn("https://timesheets.example.com/password-reset/", mail.outbox[0].body)

    def test_request_does_not_send_reset_for_pending_unusable_password_user(self):
        user = User.objects.create_user(
            username="pending-user",
            email="pending@example.com",
            role=User.Role.NANNY,
        )
        user.set_unusable_password()
        user.save(update_fields=["password"])

        response = self.client.post(
            reverse("password-reset-request-web"),
            {"email": "pending@example.com"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "If an account exists for that email, password reset instructions have been sent.")
        self.assertEqual(len(mail.outbox), 0)

    def test_user_can_reset_password_with_email_link(self):
        user = User.objects.create_user(
            username="nanny1",
            password="OldStrongPass123!",
            email="nanny@example.com",
            role=User.Role.NANNY,
        )
        self.client.post(reverse("password-reset-request-web"), {"email": "nanny@example.com"})
        reset_url = re.search(r"https://timesheets.example.com([^\s]+)", mail.outbox[0].body).group(1)

        response = self.client.post(
            reset_url,
            {
                "uidb64": reset_url.strip("/").split("/")[-2],
                "token": reset_url.strip("/").split("/")[-1],
                "password": "NewStrongPass123!",
                "confirm_password": "NewStrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Password reset complete")
        user.refresh_from_db()
        self.assertTrue(user.check_password("NewStrongPass123!"))

    def test_invalid_reset_token_does_not_change_password(self):
        user = User.objects.create_user(
            username="nanny1",
            password="OldStrongPass123!",
            email="nanny@example.com",
            role=User.Role.NANNY,
        )

        response = self.client.post(
            reverse("password-reset-confirm-web", args=["bad-uid", "bad-token"]),
            {
                "uidb64": "bad-uid",
                "token": "bad-token",
                "password": "NewStrongPass123!",
                "confirm_password": "NewStrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Password reset link is invalid or expired")
        user.refresh_from_db()
        self.assertTrue(user.check_password("OldStrongPass123!"))
