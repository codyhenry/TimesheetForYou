from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        NANNY = "nanny", "Nanny"
        ADMIN = "admin", "Admin"

    role = models.CharField(max_length=20, choices=Role.choices, blank=True)
    phone = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"
