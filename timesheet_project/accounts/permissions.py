from rest_framework.permissions import BasePermission


def has_completed_password_setup(user):
    return not getattr(user, "force_password_change", False)


class IsNanny(BasePermission):
    message = "You must change your temporary password before continuing."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_active
            and has_completed_password_setup(request.user)
            and getattr(request.user, "role", None) == "nanny"
        )


class IsDashboardUser(BasePermission):
    message = "You must change your temporary password before continuing."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and has_completed_password_setup(request.user)
            and getattr(request.user, "can_access_dashboard", False)
        )


class IsAdmin(BasePermission):
    message = "You must change your temporary password before continuing."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_active and has_completed_password_setup(request.user) and (
            getattr(request.user, "role", None) == "admin"
            or getattr(request.user, "is_staff", False)
        )
