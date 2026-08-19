from rest_framework.permissions import BasePermission


class IsNanny(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_active
            and getattr(request.user, "role", None) == "nanny"
        )


class IsDashboardUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(
            request.user, "can_access_dashboard", False
        )


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_active and (
            getattr(request.user, "role", None) == "admin"
            or getattr(request.user, "is_staff", False)
        )
