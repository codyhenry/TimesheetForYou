from rest_framework.permissions import BasePermission


PASSWORD_SETUP_MESSAGE = "You must complete password setup before continuing."


def is_password_setup_required(user):
    return getattr(user, "force_password_change", False)


def deny_if_password_setup_required(permission, user):
    if is_password_setup_required(user):
        permission.message = PASSWORD_SETUP_MESSAGE
        return True
    return False


class IsNanny(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated or not request.user.is_active:
            return False
        if deny_if_password_setup_required(self, request.user):
            return False
        return getattr(request.user, "role", None) == "nanny"


class IsDashboardUser(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if deny_if_password_setup_required(self, request.user):
            return False
        return getattr(request.user, "can_access_dashboard", False)


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated or not request.user.is_active:
            return False
        if deny_if_password_setup_required(self, request.user):
            return False
        return (
            getattr(request.user, "role", None) == "admin"
            or getattr(request.user, "is_staff", False)
        )
