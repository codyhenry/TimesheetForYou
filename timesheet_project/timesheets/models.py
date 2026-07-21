from django.conf import settings
from django.db import models


class WeeklyTimesheet(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PARTIALLY_SIGNED = "partially_signed", "Partially Signed"
        FULLY_SIGNED = "fully_signed", "Fully Signed"
        SUBMITTED_WITH_UNSIGNED_ENTRIES = "submitted_with_unsigned_entries", "Submitted With Unsigned Entries"
        SUBMITTED_FULLY_SIGNED = "submitted_fully_signed", "Submitted Fully Signed"

    nanny = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="weekly_timesheets")
    week_start_date = models.DateField()
    week_end_date = models.DateField()
    status = models.CharField(
        max_length=50, choices=Status.choices, default=Status.DRAFT)
    admin_notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    is_late_submission = models.BooleanField(default=False)
    late_submission_note = models.TextField(blank=True)
    pdf_file = models.FileField(
        upload_to="timesheet_pdfs/", null=True, blank=True)
    submission = models.OneToOneField(
        "TimesheetSubmission",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="timesheet",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("nanny", "week_start_date")
        ordering = ["-week_start_date", "-created_at"]

    def __str__(self):
        return f"{self.nanny} - {self.week_start_date}"

    @property
    def is_submitted(self):
        return self.status in {
            self.Status.SUBMITTED_FULLY_SIGNED,
            self.Status.SUBMITTED_WITH_UNSIGNED_ENTRIES,
        }


class TimesheetWeekLock(models.Model):
    week_start_date = models.DateField(unique=True)
    week_end_date = models.DateField()
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="locked_timesheet_weeks",
    )
    note = models.TextField(blank=True)
    locked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-week_start_date"]

    def __str__(self):
        return f"Locked week {self.week_start_date} - {self.week_end_date}"


class TimeEntry(models.Model):
    class SignatureStatus(models.TextChoices):
        UNSIGNED = "unsigned", "Unsigned"
        SIGNED = "signed", "Signed"
        SIGNATURE_INVALIDATED = "signature_invalidated", "Signature Invalidated"

    timesheet = models.ForeignKey(
        WeeklyTimesheet, on_delete=models.CASCADE, related_name="entries")
    work_date = models.DateField()
    family_name = models.CharField(max_length=255)
    family_requested_nanny = models.BooleanField(default=False)
    start_time = models.TimeField()
    end_time = models.TimeField()
    total_hours = models.DecimalField(max_digits=6, decimal_places=2)
    notes = models.TextField(blank=True)
    signature_status = models.CharField(
        max_length=32,
        choices=SignatureStatus.choices,
        default=SignatureStatus.UNSIGNED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["work_date", "start_time", "id"]

    def __str__(self):
        return f"{self.family_name} - {self.work_date}"

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            from .services import calculate_total_hours

            self.total_hours = calculate_total_hours(
                self.start_time, self.end_time)
        super().save(*args, **kwargs)


class ParentSignature(models.Model):
    entry = models.OneToOneField(
        TimeEntry, on_delete=models.CASCADE, related_name="parent_signature")
    image = models.ImageField(upload_to="signatures/")
    signed_at = models.DateTimeField(auto_now_add=True)
    approved_snapshot = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Signature for entry {self.entry.pk}"


class TimesheetSubmission(models.Model):
    class Status(models.TextChoices):
        SUBMITTED_WITH_UNSIGNED_ENTRIES = "submitted_with_unsigned_entries", "Submitted With Unsigned Entries"
        SUBMITTED_FULLY_SIGNED = "submitted_fully_signed", "Submitted Fully Signed"

    status = models.CharField(max_length=50, choices=Status.choices)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="timesheet_submissions",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_late_submission = models.BooleanField(default=False)
    late_submission_note = models.TextField(blank=True)
    total_hours = models.DecimalField(max_digits=8, decimal_places=2)
    pdf_file = models.FileField(upload_to="timesheet_pdfs/submissions/")
    snapshot = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-submitted_at", "-id"]

    def __str__(self):
        return f"Submission {self.pk} ({self.status})"
