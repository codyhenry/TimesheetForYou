from django.contrib import admin

from .models import ParentSignature, TimeEntry, TimesheetSubmission, TimesheetWeekLock, WeeklyTimesheet


class TimeEntryInline(admin.TabularInline):
    model = TimeEntry
    extra = 0


@admin.register(WeeklyTimesheet)
class WeeklyTimesheetAdmin(admin.ModelAdmin):
    list_display = ("id", "nanny", "week_start_date", "week_end_date", "status", "submitted_at")
    list_filter = ("status", "week_start_date")
    search_fields = ("nanny__username", "nanny__first_name", "nanny__last_name")
    inlines = [TimeEntryInline]


@admin.register(TimesheetWeekLock)
class TimesheetWeekLockAdmin(admin.ModelAdmin):
    list_display = ("week_start_date", "week_end_date", "locked_by", "locked_at")
    list_filter = ("week_start_date", "locked_at")
    search_fields = ("locked_by__username", "locked_by__first_name", "locked_by__last_name", "note")
    readonly_fields = ("locked_at",)


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ("id", "timesheet", "work_date", "family_name", "start_time", "end_time", "total_hours", "signature_status")
    list_filter = ("signature_status", "work_date", "family_name")


@admin.register(ParentSignature)
class ParentSignatureAdmin(admin.ModelAdmin):
    list_display = ("id", "entry", "signed_at")


@admin.register(TimesheetSubmission)
class TimesheetSubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "submitted_by", "submitted_at", "total_hours")
