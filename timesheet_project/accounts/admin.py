from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.admin import GroupAdmin, UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

from .models import User


RESTRICTED_PERMISSION_FIELDS = {"password", "is_staff", "is_superuser", "groups", "user_permissions"}


def _filter_restricted_fields(fields):
    filtered = []
    for field in fields:
        if isinstance(field, (list, tuple)):
            nested_fields = tuple(
                nested_field
                for nested_field in field
                if nested_field not in RESTRICTED_PERMISSION_FIELDS
            )
            if nested_fields:
                filtered.append(nested_fields)
        elif field not in RESTRICTED_PERMISSION_FIELDS:
            filtered.append(field)
    return tuple(filtered)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = [
        *(BaseUserAdmin.fieldsets or []),
        ("Profile", {"fields": ("role", "phone")}),
    ]
    add_fieldsets = [
        *(BaseUserAdmin.add_fieldsets or []),
        ("Profile", {"fields": ("role", "phone")}),
    ]
    list_display = (
        "username",
        "first_name",
        "last_name",
        "email",
        "role",
        "is_active",
        "is_staff",
    )
    list_filter = ("role", "is_staff", "is_superuser", "is_active")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.filter(is_superuser=False)

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if request.user.is_superuser:
            return fieldsets

        safe_fieldsets = []
        for title, options in fieldsets:
            safe_options = {**options}
            safe_fields = _filter_restricted_fields(safe_options.get("fields", ()))
            if safe_fields:
                safe_options["fields"] = safe_fields
                safe_fieldsets.append((title, safe_options))
        return safe_fieldsets

    def get_list_filter(self, request):
        list_filter = super().get_list_filter(request)
        if request.user.is_superuser:
            return list_filter
        return tuple(
            field for field in list_filter if field not in {"is_staff", "is_superuser"}
        )

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            if change:
                original = User.objects.get(pk=obj.pk)
                obj.password = original.password
                obj.is_staff = original.is_staff
                obj.is_superuser = original.is_superuser
            else:
                obj.set_unusable_password()
                obj.is_staff = False
                obj.is_superuser = False
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        has_permission = super().has_change_permission(request, obj)
        if not has_permission:
            return False
        if obj is not None and not request.user.is_superuser and obj.is_superuser:
            return False
        return True

    def has_view_permission(self, request, obj=None):
        has_permission = super().has_view_permission(request, obj)
        if not has_permission:
            return False
        if obj is not None and not request.user.is_superuser and obj.is_superuser:
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)


class SafeGroupAdmin(GroupAdmin):
    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


try:
    admin.site.unregister(Group)
except NotRegistered:
    pass
admin.site.register(Group, SafeGroupAdmin)
