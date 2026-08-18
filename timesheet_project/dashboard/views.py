from decimal import Decimal

from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from timesheets.models import TimeEntry, WeeklyTimesheet
from timesheets.services import (
    filter_submitted_timesheets,
    get_request_incentive_groups_for_timesheet,
    get_timesheet_entry_prefetch,
    get_timesheet_request_incentive_count,
    get_timesheet_week_range,
)


admin_required = user_passes_test(
    lambda user: user.is_authenticated and (
        getattr(user, "role", None) == "admin" or getattr(user, "is_staff", False))
)


INDICATOR_DEFINITIONS = {
    "unsigned": {
        "icon": "⚠️",
        "label": "Unsigned entries",
        "tooltip": "Submitted with unsigned or invalidated entries.",
    },
    "late": {
        "icon": "⏰",
        "label": "Late submission",
        "tooltip": "Submitted after the Saturday noon deadline.",
    },
    "incentive": {
        "icon": "🎁",
        "label": "Request incentive",
        "tooltip": "This timesheet contains a 5-request incentive milestone.",
    },
}


def _submitted_timesheet_queryset():
    return WeeklyTimesheet.objects.filter(submission__isnull=False).select_related(
        "nanny", "submission"
    ).prefetch_related(get_timesheet_entry_prefetch())


def _current_week_start():
    week_start, _ = get_timesheet_week_range(timezone.localdate())
    return week_start


def _get_filter_params(request):
    params = request.GET.copy()
    if "week_start" not in request.GET:
        params["week_start"] = _current_week_start().isoformat()
    return params


def _filtered_queryset(request):
    return filter_submitted_timesheets(
        _submitted_timesheet_queryset(), _get_filter_params(request)
    )


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


def _format_short_date(value):
    return f"{value.month}.{value.day}.{value.year % 100:02d}"


def _format_week_range(timesheet):
    return f"{_format_short_date(timesheet.week_start_date)} - {_format_short_date(timesheet.week_end_date)}"


def _get_week_options():
    week_rows = list(
        _submitted_timesheet_queryset()
        .values("week_start_date", "week_end_date")
        .distinct()
        .order_by("-week_start_date")
    )
    current_week_start = _current_week_start()
    if not any(row["week_start_date"] == current_week_start for row in week_rows):
        current_start, current_end = get_timesheet_week_range(current_week_start)
        week_rows.insert(
            0,
            {
                "week_start_date": current_start,
                "week_end_date": current_end,
            },
        )
    return [
        {
            "value": row["week_start_date"].isoformat(),
            "label": f'{_format_short_date(row["week_start_date"])} - {_format_short_date(row["week_end_date"])}',
        }
        for row in week_rows
    ]


def _get_status_counts(queryset):
    status_labels = dict(WeeklyTimesheet.Status.choices)
    return [
        {
            "status": row["status"],
            "label": status_labels.get(row["status"], row["status"]),
            "count": row["count"],
        }
        for row in queryset.values("status").annotate(count=Count("id")).order_by("status")
    ]


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


def _has_unsigned_entries(timesheet):
    return timesheet.dashboard_unsigned_entry_count > 0


def _get_dashboard_indicators(timesheet):
    indicators = []
    if _has_unsigned_entries(timesheet):
        indicators.append(INDICATOR_DEFINITIONS["unsigned"])
    if timesheet.is_late_submission:
        indicators.append(INDICATOR_DEFINITIONS["late"])
    if get_timesheet_request_incentive_count(timesheet) > 0:
        indicators.append(INDICATOR_DEFINITIONS["incentive"])
    return indicators


def _prepare_dashboard_timesheets(queryset):
    timesheets = list(queryset)
    for timesheet in timesheets:
        entries = list(timesheet.entries.all())
        signed_count = sum(
            1 for entry in entries if entry.signature_status == TimeEntry.SignatureStatus.SIGNED
        )
        unsigned_count = sum(
            1
            for entry in entries
            if entry.signature_status in {
                TimeEntry.SignatureStatus.UNSIGNED,
                TimeEntry.SignatureStatus.SIGNATURE_INVALIDATED,
            }
        )
        nanny_name = timesheet.nanny.get_full_name() or timesheet.nanny.username
        timesheet.dashboard_title = f"{nanny_name} — {_format_week_range(timesheet)}"
        timesheet.dashboard_week_label = _format_week_range(timesheet)
        timesheet.dashboard_total_hours = sum(
            (entry.total_hours for entry in entries), Decimal("0.00")
        )
        timesheet.dashboard_signed_entry_count = signed_count
        timesheet.dashboard_unsigned_entry_count = unsigned_count
        timesheet.dashboard_indicators = _get_dashboard_indicators(timesheet)
        timesheet.dashboard_request_incentive_groups = get_request_incentive_groups_for_timesheet(timesheet)
    return timesheets


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
        "status_counts": _get_status_counts(queryset),
        "total_hours": queryset.aggregate(total=Sum("entries__total_hours"))["total"] or Decimal("0.00"),
        "timesheet_count": queryset.count(),
    }
    return render(
        request,
        "dashboard/index.html",
        {
            "timesheets": _prepare_dashboard_timesheets(queryset),
            "selected_timesheet": selected_timesheet,
            "stats": stats,
            "filters": _get_filter_params(request),
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
    return redirect("dashboard-index")
