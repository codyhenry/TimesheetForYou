from pathlib import Path

from django.contrib import admin

from .models import ParentSignature, TimeEntry, TimesheetSubmission, TimesheetWeekLock, WeeklyTimesheet
from .signatures import replace_parent_signature_image


class TimeEntryInline(admin.TabularInline):
    model = TimeEntry
    extra = 0
    fields = (
        "work_date",
        "family_name",
        "family_requested_nanny",
        "start_time",
        "end_time",
        "total_hours",
        "signature_status",
    )


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
    list_display = (
        "id",
        "timesheet",
        "work_date",
        "family_name",
        "family_requested_nanny",
        "start_time",
        "end_time",
        "total_hours",
        "signature_status",
    )
    list_filter = ("signature_status", "family_requested_nanny", "work_date", "family_name")


@admin.register(ParentSignature)
class ParentSignatureAdmin(admin.ModelAdmin):
    list_display = ("id", "entry", "signed_at")
    readonly_fields = ("signed_at",)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj and "entry" not in readonly_fields:
            readonly_fields.append("entry")
        return readonly_fields

    def save_model(self, request, obj, form, change):
        if "image" in form.changed_data:
            image_name = Path(obj.image.name).name
            replacement = replace_parent_signature_image(
                entry_id=obj.entry_id,
                signature_id=obj.pk if change else None,
                image_name=image_name,
                image_content=obj.image.file,
                approved_snapshot=obj.approved_snapshot,
            )
            obj.pk = replacement.pk
            obj.entry = replacement.entry
            obj.image = replacement.image
            obj.signed_at = replacement.signed_at
            return

        super().save_model(request, obj, form, change)


@admin.register(TimesheetSubmission)
class TimesheetSubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "submitted_by", "submitted_at", "total_hours")
