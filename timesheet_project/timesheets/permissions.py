from rest_framework.permissions import BasePermission


class IsTimesheetOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and obj.nanny_id == request.user.pk


class IsEntryOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and obj.timesheet.nanny_id == request.user.pk
