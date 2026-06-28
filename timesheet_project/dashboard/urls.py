from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="dashboard-index"),
    path("timesheets/<int:timesheet_id>/", views.index, name="dashboard-detail"),
    path("timesheets/<int:timesheet_id>/notes/", views.update_notes, name="dashboard-notes"),
]
