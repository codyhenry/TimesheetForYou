from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


GENERIC_PASSWORD_RESET_MESSAGE = "If an account exists for that email, password reset instructions have been sent."


def build_password_reset_url(user):
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    base_url = settings.SITE_BASE_URL.rstrip("/")
    reset_path = reverse("password-reset-confirm-web", args=[uidb64, token])
    return f"{base_url}{reset_path}"


def send_user_password_reset_email(user):
    if not user.is_active or not user.email or not user.has_usable_password():
        return False

    reset_url = build_password_reset_url(user)
    send_mail(
        subject="Reset your Timesheet password",
        message=(
            f"Hi {user.first_name or user.get_full_name() or 'there'},\n\n"
            "Use the link below to reset your Timesheet password.\n\n"
            f"{reset_url}\n\n"
            "If you did not request this, you can ignore this email."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return True
