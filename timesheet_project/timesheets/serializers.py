from decimal import Decimal

from rest_framework import serializers

from accounts.models import User
from .models import ParentSignature, TimeEntry, TimesheetSubmission, TimesheetWeekLock, WeeklyTimesheet
from .services import calculate_total_hours, is_timesheet_week_locked


class NannySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name",
                  "last_name", "email", "phone", "role"]


class ParentSignatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentSignature
        fields = ["id", "image", "signed_at", "approved_snapshot"]
        read_only_fields = fields


class TimeEntrySerializer(serializers.ModelSerializer):
    has_signature = serializers.SerializerMethodField()
    parent_signature = ParentSignatureSerializer(read_only=True)

    class Meta:
        model = TimeEntry
        fields = [
            "id",
            "timesheet",
            "work_date",
            "family_name",
            "start_time",
            "end_time",
            "total_hours",
            "notes",
            "signature_status",
            "has_signature",
            "parent_signature",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["timesheet", "total_hours",
                            "signature_status", "created_at", "updated_at"]

    def get_has_signature(self, obj):
        return obj.signature_status == TimeEntry.SignatureStatus.SIGNED and hasattr(obj, "parent_signature")

    def validate(self, attrs):
        timesheet = self.context.get("timesheet") or getattr(
            self.instance, "timesheet", None)
        work_date = attrs.get("work_date", getattr(
            self.instance, "work_date", None))
        start_time = attrs.get("start_time", getattr(
            self.instance, "start_time", None))
        end_time = attrs.get("end_time", getattr(
            self.instance, "end_time", None))
        family_name = attrs.get("family_name", getattr(
            self.instance, "family_name", ""))

        if timesheet and work_date and not (timesheet.week_start_date <= work_date <= timesheet.week_end_date):
            raise serializers.ValidationError(
                {"work_date": "Entry date must fall within the timesheet week."})
        if family_name is not None and not str(family_name).strip():
            raise serializers.ValidationError(
                {"family_name": "Family name is required."})
        if start_time and end_time:
            attrs["total_hours"] = calculate_total_hours(start_time, end_time)
        return attrs


class TimesheetSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimesheetSubmission
        fields = [
            "id",
            "status",
            "submitted_by",
            "submitted_at",
            "is_late_submission",
            "late_submission_note",
            "total_hours",
            "pdf_file",
            "snapshot",
        ]
        read_only_fields = fields


class TimesheetWeekLockSerializer(serializers.ModelSerializer):
    locked_by = NannySummarySerializer(read_only=True)

    class Meta:
        model = TimesheetWeekLock
        fields = ["id", "week_start_date", "week_end_date", "locked_by", "note", "locked_at"]
        read_only_fields = fields


class WeeklyTimesheetListSerializer(serializers.ModelSerializer):
    total_hours = serializers.SerializerMethodField()
    signed_entry_count = serializers.SerializerMethodField()
    unsigned_entry_count = serializers.SerializerMethodField()
    total_hours_by_family = serializers.SerializerMethodField()
    is_week_locked = serializers.SerializerMethodField()

    class Meta:
        model = WeeklyTimesheet
        fields = [
            "id",
            "week_start_date",
            "week_end_date",
            "status",
            "submitted_at",
            "is_late_submission",
            "late_submission_note",
            "is_week_locked",
            "total_hours",
            "signed_entry_count",
            "unsigned_entry_count",
            "total_hours_by_family",
            "admin_notes",
        ]

    def _entries(self, obj):
        prefetched = getattr(
            obj, "_prefetched_objects_cache", {}).get("entries")
        if prefetched is not None:
            return prefetched
        return list(obj.entries.all())

    def get_total_hours(self, obj):
        return sum((entry.total_hours for entry in self._entries(obj)), Decimal("0.00"))

    def get_signed_entry_count(self, obj):
        return sum(1 for entry in self._entries(obj) if entry.signature_status == TimeEntry.SignatureStatus.SIGNED)

    def get_unsigned_entry_count(self, obj):
        return sum(
            1
            for entry in self._entries(obj)
            if entry.signature_status in {TimeEntry.SignatureStatus.UNSIGNED, TimeEntry.SignatureStatus.SIGNATURE_INVALIDATED}
        )

    def get_total_hours_by_family(self, obj):
        totals = {}
        for entry in self._entries(obj):
            totals.setdefault(entry.family_name, Decimal("0.00"))
            totals[entry.family_name] += entry.total_hours
        return [{"family_name": family_name, "total_hours": total_hours} for family_name, total_hours in totals.items()]

    def get_is_week_locked(self, obj):
        return is_timesheet_week_locked(obj)


class WeeklyTimesheetDetailSerializer(WeeklyTimesheetListSerializer):
    entries = TimeEntrySerializer(many=True, read_only=True)
    submission = TimesheetSubmissionSerializer(read_only=True)

    class Meta(WeeklyTimesheetListSerializer.Meta):
        fields = WeeklyTimesheetListSerializer.Meta.fields + \
            ["entries", "submission"]


class AdminTimesheetListSerializer(WeeklyTimesheetListSerializer):
    nanny = NannySummarySerializer(read_only=True)

    class Meta(WeeklyTimesheetListSerializer.Meta):
        fields = ["id", "nanny", "week_start_date", "week_end_date", "status",
                  "submitted_at", "is_late_submission", "is_week_locked", "total_hours", "signed_entry_count", "unsigned_entry_count"]


class AdminTimesheetDetailSerializer(WeeklyTimesheetDetailSerializer):
    nanny = NannySummarySerializer(read_only=True)

    class Meta(WeeklyTimesheetDetailSerializer.Meta):
        fields = ["id", "nanny", "week_start_date", "week_end_date", "status", "submitted_at", "is_late_submission", "late_submission_note", "is_week_locked", "admin_notes",
                  "total_hours", "signed_entry_count", "unsigned_entry_count", "total_hours_by_family", "entries", "submission"]


class AdminNotesUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeeklyTimesheet
        fields = ["admin_notes"]
