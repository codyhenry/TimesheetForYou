from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        NANNY = "nanny", "Nanny"
        OFFICE = "office", "Office"
        ADMIN = "admin", "Admin"

    role = models.CharField(max_length=20, choices=Role.choices, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    force_password_change = models.BooleanField(default=False)

    @property
    def can_access_dashboard(self):
        return self.is_active and (
            self.role in {self.Role.OFFICE, self.Role.ADMIN}
            or self.is_staff
            or self.is_superuser
        )

    @property
    def can_access_django_admin(self):
        return self.is_active and self.is_staff

    @property
    def account_setup_required(self):
        return self.is_active and not self.has_usable_password()

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"


class AccountSetupToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="account_setup_tokens",
    )
    token_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "used_at", "expires_at"]),
        ]

    @property
    def is_available(self):
        return self.used_at is None and self.expires_at > timezone.now()

    def mark_used(self):
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])
