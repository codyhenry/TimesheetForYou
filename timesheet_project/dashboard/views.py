import logging
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Count, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from accounts.services import send_account_setup_email
from dashboard.forms import (
    MANAGED_ROLE_CHOICES,
    MANAGED_ROLES,
    DashboardManagedUserCreateForm,
    DashboardManagedUserUpdateForm,
)
from timesheets.models import TimeEntry, WeeklyTimesheet
from timesheets.services import (
    filter_submitted_timesheets,
    get_request_incentive_groups_for_timesheet,
    get_timesheet_entry_prefetch,
    get_timesheet_week_range,
)

logger = logging.getLogger(__name__)


dashboard_user_required = user_passes_test(
    lambda user: user.is_authenticated and getattr(user, "can_access_dashboard", False)
)
dashboard_admin_required = user_passes_test(
    lambda user: user.is_authenticated
    and user.is_active
    and (
        getattr(user, "role", None) == User.Role.ADMIN
        or getattr(user, "is_staff", False)
    )
)


def _dashboard_password_ready_required(view_func):
    @dashboard_user_required
    def wrapped(request, *args, **kwargs):
        if getattr(request.user, "force_password_change", False):
            return redirect("dashboard-password-setup")
        return view_func(request, *args, **kwargs)

    return wrapped


def _dashboard_admin_password_ready_required(view_func):
    @dashboard_admin_required
    def wrapped(request, *args, **kwargs):
        if getattr(request.user, "force_password_change", False):
            return redirect("dashboard-password-setup")
        return view_func(request, *args, **kwargs)

    return wrapped


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

    incentive_count = getattr(timesheet, "dashboard_request_incentive_count", None)
    if incentive_count is None:
        incentive_count = len(get_request_incentive_groups_for_timesheet(timesheet))
    if incentive_count > 0:
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
        incentive_groups = get_request_incentive_groups_for_timesheet(timesheet)
        nanny_name = timesheet.nanny.get_full_name() or timesheet.nanny.username
        timesheet.dashboard_title = f"{nanny_name} — {_format_week_range(timesheet)}"
        timesheet.dashboard_week_label = _format_week_range(timesheet)
        timesheet.dashboard_total_hours = sum(
            (entry.total_hours for entry in entries), Decimal("0.00")
        )
        timesheet.dashboard_signed_entry_count = signed_count
        timesheet.dashboard_unsigned_entry_count = unsigned_count
        timesheet.dashboard_request_incentive_groups = incentive_groups
        timesheet.dashboard_request_incentive_count = len(incentive_groups)
        timesheet.dashboard_indicators = _get_dashboard_indicators(timesheet)
    return timesheets


def _managed_user_queryset():
    return User.objects.filter(role__in=MANAGED_ROLES, is_superuser=False).order_by(
        "role", "last_name", "first_name", "username"
    )


def _get_managed_user(pk):
    return get_object_or_404(_managed_user_queryset(), pk=pk)


def _get_update_form_prefix(user):
    return f"user-{user.pk}"


def _get_posted_managed_user(request):
    user_id = request.POST.get("user_id")
    try:
        user_pk = int(user_id)
    except (TypeError, ValueError):
        raise Http404("Managed user not found.")
    return _get_managed_user(user_pk)


def _normalize_update_post_data(request, user):
    prefix = _get_update_form_prefix(user)
    data = request.POST.copy()

    if f"{prefix}-role" in request.POST:
        return data

    for field_name in [
        "first_name",
        "last_name",
        "email",
        "phone",
        "role",
    ]:
        if field_name in request.POST:
            data[f"{prefix}-{field_name}"] = request.POST.get(field_name, "")

    if "is_active" in request.POST:
        data[f"{prefix}-is_active"] = request.POST.get("is_active")

    return data


def _render_user_management(request, create_form=None, update_form=None, update_user=None):
    users = list(_managed_user_queryset())
    return render(
        request,
        "dashboard/users.html",
        {
            "create_form": create_form or DashboardManagedUserCreateForm(initial={"is_active": True}),
            "update_form": update_form,
            "update_user": update_user,
            "nannies": [user for user in users if user.role == User.Role.NANNY],
            "dashboard_users": [
                user for user in users if user.role in {User.Role.OFFICE, User.Role.ADMIN}
            ],
            "role_choices": MANAGED_ROLE_CHOICES,
        },
    )


@dashboard_user_required
def password_setup(request):
    if not getattr(request.user, "force_password_change", False):
        return redirect("dashboard-index")

    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        user.force_password_change = False
        user.save(update_fields=["force_password_change"])
        update_session_auth_hash(request, user)
        return redirect("dashboard-index")

    return render(request, "dashboard/password_setup.html", {"form": form})


@_dashboard_password_ready_required
def index(request, timesheet_id=None):
    queryset = _filtered_queryset(request)

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
            "stats": stats,
            "filters": _get_filter_params(request),
            "filter_options": _get_filter_options(request),
        },
    )


@_dashboard_admin_password_ready_required
def user_management(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            form = DashboardManagedUserCreateForm(request.POST)
            if form.is_valid():
                user = form.save()
                setup_token = None
                email_failed = False
                if user.is_active:
                    try:
                        setup_token = send_account_setup_email(user)
                    except Exception:
                        email_failed = True
                        logger.exception("Failed to send account setup email for user %s", user.pk)
                display_name = user.get_full_name() or user.email or user.username
                if setup_token:
                    messages.success(request, f"Created {display_name} and sent setup instructions.")
                elif email_failed:
                    messages.warning(
                        request,
                        f"Created {display_name}, but setup instructions could not be sent. Check email configuration and resend the setup invite.",
                    )
                elif not user.is_active:
                    messages.success(
                        request,
                        f"Created {display_name}. Setup instructions were not sent because the account is inactive.",
                    )
                else:
                    messages.warning(
                        request,
                        f"Created {display_name}, but setup instructions were not sent because the account has no email address.",
                    )
                return redirect("dashboard-users")
            return _render_user_management(request, create_form=form)

        if action == "update":
            user = _get_posted_managed_user(request)
            form = DashboardManagedUserUpdateForm(
                _normalize_update_post_data(request, user),
                instance=user,
                prefix=_get_update_form_prefix(user),
            )
            if form.is_valid():
                user = form.save()
                messages.success(request, f"Updated {user.get_full_name() or user.username}.")
                return redirect("dashboard-users")
            return _render_user_management(request, update_form=form, update_user=user)

        messages.error(request, "Unknown user management action.")
        return redirect("dashboard-users")

    return _render_user_management(request)


@_dashboard_password_ready_required
def update_notes(request, timesheet_id):
    timesheet = get_object_or_404(WeeklyTimesheet.objects.filter(
        submission__isnull=False), pk=timesheet_id)
    if request.method == "POST":
        timesheet.admin_notes = request.POST.get("admin_notes", "")
        timesheet.save(update_fields=["admin_notes", "updated_at"])

    dashboard_url = reverse("dashboard-index")
    return redirect(f"{dashboard_url}?week_start={timesheet.week_start_date.isoformat()}")
