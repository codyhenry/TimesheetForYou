from decimal import Decimal

from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from timesheets.models import WeeklyTimesheet
from timesheets.services import filter_submitted_timesheets, get_timesheet_entry_prefetch


admin_required = user_passes_test(
    lambda user: user.is_authenticated and (
        getattr(user, "role", None) == "admin" or getattr(user, "is_staff", False))
)


def _submitted_timesheet_queryset():
    return WeeklyTimesheet.objects.filter(submission__isnull=False).select_related(
        "nanny", "submission"
    ).prefetch_related(get_timesheet_entry_prefetch())


def _filtered_queryset(request):
    return filter_submitted_timesheets(_submitted_timesheet_queryset(), request.GET)


def _get_nanny_options(request):
    nanny_status = request.GET.get("nanny_status", "active")
    selected_nanny_id = request.GET.get("nanny")
    nannies = User.objects.filter(role=User.Role.NANNY).order_by(
        "last_name", "first_name", "username"
    )

    if nanny_status == "inactive":
        nannies = nannies.filter(is_active=False)
    elif nanny_status != "all":
        nannies = nannies.filter(is_active=True)

    if selected_nanny_id and not nannies.filter(pk=selected_nanny_id).exists():
        selected_nanny = User.objects.filter(
            role=User.Role.NANNY,
            pk=selected_nanny_id,
        ).first()
        if selected_nanny:
            nannies = list(nannies)
            nannies.append(selected_nanny)

    return nannies


def _get_week_options():
    return list(
        _submitted_timesheet_queryset()
        .values("week_start_date", "week_end_date")
        .distinct()
        .order_by("-week_start_date")
    )


def _get_filter_options(request):
    return {
        "nannies": _get_nanny_options(request),
        "nanny_status": request.GET.get("nanny_status", "active"),
        "nanny_statuses": [
            {"value": "active", "label": "Active nannies"},
            {"value": "inactive", "label": "Inactive nannies"},
            {"value": "all", "label": "All nannies"},
        ],
        "statuses": WeeklyTimesheet.Status.choices,
        "weeks": _get_week_options(),
    }


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
            "filter_options": _get_filter_options(request),
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
