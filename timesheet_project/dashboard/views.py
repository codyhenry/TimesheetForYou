from decimal import Decimal

from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render

from timesheets.models import WeeklyTimesheet
from timesheets.services import filter_submitted_timesheets, get_timesheet_entry_prefetch


admin_required = user_passes_test(
    lambda user: user.is_authenticated and (
        getattr(user, "role", None) == "admin" or user.is_staff)
)


def _filtered_queryset(request):
    queryset = WeeklyTimesheet.objects.filter(submission__isnull=False).select_related(
        "nanny", "submission").prefetch_related(get_timesheet_entry_prefetch())
    return filter_submitted_timesheets(queryset, request.GET)


@admin_required
def index(request, timesheet_id=None):
    queryset = _filtered_queryset(request)
    selected_timesheet = None
    if timesheet_id:
        selected_timesheet = get_object_or_404(queryset, pk=timesheet_id)
    elif request.GET.get("timesheet"):
        selected_timesheet = get_object_or_404(
            queryset, pk=request.GET["timesheet"])

    stats = {
        "status_counts": list(queryset.values("status").annotate(count=Count("id")).order_by("status")),
        "total_hours": queryset.aggregate(total=Sum("entries__total_hours"))["total"] or Decimal("0.00"),
        "timesheet_count": queryset.count(),
    }
    return render(
        request,
        "dashboard/index.html",
        {
            "timesheets": queryset,
            "selected_timesheet": selected_timesheet,
            "stats": stats,
            "filters": request.GET,
        },
    )


@admin_required
def update_notes(request, timesheet_id):
    timesheet = get_object_or_404(WeeklyTimesheet.objects.filter(
        submission__isnull=False), pk=timesheet_id)
    if request.method == "POST":
        timesheet.admin_notes = request.POST.get("admin_notes", "")
        timesheet.save(update_fields=["admin_notes", "updated_at"])
    return redirect("dashboard-detail", timesheet_id=timesheet_id)
