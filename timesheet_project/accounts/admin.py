from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = [*(BaseUserAdmin.fieldsets or []),
                 ("Profile", {"fields": ("role", "phone")})]
    list_display = ("username", "first_name", "last_name",
                    "email", "role", "is_staff")
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
