from django.contrib.auth.models import AbstractUser
from django.db import models


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

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"
