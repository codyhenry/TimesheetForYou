from rest_framework.permissions import BasePermission


TEMPORARY_PASSWORD_MESSAGE = "You must change your temporary password before continuing."


def is_password_setup_required(user):
    return getattr(user, "force_password_change", False)


def has_completed_password_setup(user):
    return not is_password_setup_required(user)


def deny_if_password_setup_required(permission, user):
    if is_password_setup_required(user):
        permission.message = TEMPORARY_PASSWORD_MESSAGE
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
