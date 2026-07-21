from django.urls import path

from .views import AdminTimesheetViewSet, SignatureView, TimeEntryViewSet, TimesheetViewSet

timesheet_list = TimesheetViewSet.as_view({"get": "list"})
timesheet_current = TimesheetViewSet.as_view({"get": "current"})
timesheet_detail = TimesheetViewSet.as_view({"get": "retrieve"})
timesheet_submit = TimesheetViewSet.as_view({"post": "submit"})
timesheet_pdf = TimesheetViewSet.as_view({"get": "pdf"})
entry_list_create = TimeEntryViewSet.as_view({"get": "list", "post": "create"})
entry_detail = TimeEntryViewSet.as_view(
    {"get": "retrieve", "patch": "partial_update", "delete": "destroy"})
admin_timesheet_list = AdminTimesheetViewSet.as_view({"get": "list"})
admin_timesheet_detail = AdminTimesheetViewSet.as_view({"get": "retrieve"})
admin_timesheet_pdf = AdminTimesheetViewSet.as_view({"get": "pdf"})
admin_timesheet_notes = AdminTimesheetViewSet.as_view({"patch": "notes"})
admin_timesheet_override_submit = AdminTimesheetViewSet.as_view(
    {"post": "override_submit"})
admin_timesheet_lock_week = AdminTimesheetViewSet.as_view(
    {"post": "lock_week"})

urlpatterns = [
    path("timesheets/current/", timesheet_current, name="timesheet-current"),
    path("timesheets/", timesheet_list, name="timesheet-list"),
    path("timesheets/<int:pk>/", timesheet_detail, name="timesheet-detail"),
    path("timesheets/<int:pk>/submit/",
         timesheet_submit, name="timesheet-submit"),
    path("timesheets/<int:pk>/pdf/", timesheet_pdf, name="timesheet-pdf"),
    path("timesheets/<int:timesheet_id>/entries/",
         entry_list_create, name="entry-list-create"),
    path("entries/<int:pk>/", entry_detail, name="entry-detail"),
    path("entries/<int:pk>/signature/",
         SignatureView.as_view(), name="entry-signature"),
    path("admin/timesheets/", admin_timesheet_list, name="admin-timesheet-list"),
    path("admin/timesheets/weeks/lock/",
         admin_timesheet_lock_week, name="admin-timesheet-lock-week"),
    path("admin/timesheets/<int:pk>/", admin_timesheet_detail,
         name="admin-timesheet-detail"),
    path("admin/timesheets/<int:pk>/pdf/",
         admin_timesheet_pdf, name="admin-timesheet-pdf"),
    path("admin/timesheets/<int:pk>/notes/",
         admin_timesheet_notes, name="admin-timesheet-notes"),
    path("admin/timesheets/<int:pk>/override-submit/",
         admin_timesheet_override_submit, name="admin-timesheet-override-submit"),
]
