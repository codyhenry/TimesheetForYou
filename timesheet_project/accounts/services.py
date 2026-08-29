import hashlib
import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone

from .models import AccountSetupToken, User


GENERIC_SETUP_REQUEST_MESSAGE = "If an account is eligible for setup, instructions have been sent."


def generate_pending_username():
    """Create a unique internal username for an account awaiting user setup."""
    while True:
        username = f"pending-{uuid.uuid4().hex[:24]}"
        if not User.objects.filter(username=username).exists():
            return username


def hash_setup_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_account_setup_token(user):
    AccountSetupToken.objects.filter(user=user, used_at__isnull=True).update(used_at=timezone.now())
    raw_token = secrets.token_urlsafe(32)
    token = AccountSetupToken.objects.create(
        user=user,
        token_hash=hash_setup_token(raw_token),
        expires_at=timezone.now() + timedelta(days=settings.ACCOUNT_SETUP_TOKEN_DAYS),
    )
    return raw_token, token


def get_available_account_setup_token(raw_token):
    if not raw_token:
        return None
    token_hash = hash_setup_token(raw_token)
    token = (
        AccountSetupToken.objects.select_related("user")
        .filter(token_hash=token_hash, used_at__isnull=True, expires_at__gt=timezone.now())
        .first()
    )
    if token is None or not token.user.is_active or token.user.has_usable_password():
        return None
    return token


def build_account_setup_url(raw_token):
    base_url = settings.ACCOUNT_SETUP_BASE_URL.rstrip("/")
    setup_path = reverse("account-setup-validate")
    return f"{base_url}{setup_path}?token={raw_token}"


def send_account_setup_email(user):
    if not user.is_active or user.has_usable_password() or not user.email:
        return None

    raw_token, token = create_account_setup_token(user)
    setup_url = build_account_setup_url(raw_token)
    send_mail(
        subject="Set up your Timesheet account",
        message=(
            f"Hi {user.first_name or user.get_full_name() or 'there'},\n\n"
            "You have been invited to set up your Timesheet account. "
            "Use the link below to choose your username and password.\n\n"
            f"{setup_url}\n\n"
            f"This link expires in {settings.ACCOUNT_SETUP_TOKEN_DAYS} days."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return token


def send_setup_email_for_identifier(identifier):
    lookup_value = (identifier or "").strip()
    if not lookup_value:
        return False

    user = (
        User.objects.filter(is_active=True, email__iexact=lookup_value)
        .exclude(email="")
        .first()
    )
    if user is None:
        user = User.objects.filter(is_active=True, phone=lookup_value).exclude(phone="").first()

    if user is None or user.has_usable_password():
        return False

    return send_account_setup_email(user) is not None
