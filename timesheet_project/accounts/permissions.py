from rest_framework.permissions import BasePermission


class IsNanny(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "nanny"


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.role == "admin" or request.user.is_staff)
