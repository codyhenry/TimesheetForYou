import base64
import binascii
from typing import Any, cast

from django.core.files.base import ContentFile
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsDashboardUser, IsNanny
from .permissions import IsEntryOwner, IsTimesheetOwner
from .models import TimeEntry, WeeklyTimesheet
from .serializers import (
    AdminNotesUpdateSerializer,
    AdminTimesheetDetailSerializer,
    AdminTimesheetListSerializer,
    ParentSignatureSerializer,
    TimeEntrySerializer,
    TimesheetWeekLockSerializer,
    WeeklyTimesheetDetailSerializer,
    WeeklyTimesheetListSerializer,
)
from .services import (
    ensure_timesheet_week_unlocked,
    filter_submitted_timesheets,
    format_timesheet_pdf_filename,
    generate_timesheet_pdf,
    get_or_create_current_week_timesheet,
    get_timesheet_entry_prefetch,
    invalidate_signature_if_needed,
    lock_timesheet_week,
    submit_timesheet,
    update_timesheet_status,
)
from .signatures import replace_parent_signature_image


def _is_truthy(value):
    return value in {True, "true", "True", "1", 1}


def _pdf_file_response(timesheet):
    filename = format_timesheet_pdf_filename(timesheet)
    return FileResponse(
        timesheet.pdf_file.open("rb"),
        content_type="application/pdf",
        filename=filename,
    )


def _clean_request_text(value, default=""):
    text = "" if value is None else str(value).strip()
    return text or default


class TimesheetViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsNanny, IsTimesheetOwner]

    def get_queryset(self):
        return WeeklyTimesheet.objects.filter(nanny=self.request.user).select_related("submission").prefetch_related(get_timesheet_entry_prefetch())

    def get_serializer_class(self):
        if self.action in {"retrieve", "current", "submit"}:
            return WeeklyTimesheetDetailSerializer
        return WeeklyTimesheetListSerializer

    @action(detail=False, methods=["get"], url_path="current")
    def current(self, request):
        timesheet, _ = get_or_create_current_week_timesheet(request.user)
        serializer = self.get_serializer(timesheet)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        timesheet = self.get_object()
        timesheet = submit_timesheet(timesheet, submitted_by=request.user)
        serializer = self.get_serializer(timesheet)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="pdf")
    def pdf(self, request, pk=None):
        timesheet = self.get_object()
        if timesheet.pdf_file:
            try:
                return _pdf_file_response(timesheet)
            except FileNotFoundError:
                pass
        pdf_bytes = generate_timesheet_pdf(timesheet)
        filename = format_timesheet_pdf_filename(timesheet)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        return response


class TimeEntryViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = TimeEntrySerializer
    permission_classes = [IsNanny, IsEntryOwner]

    def get_queryset(self):
        return TimeEntry.objects.filter(timesheet__nanny=self.request.user).select_related("timesheet", "parent_signature")

    def get_serializer_context(self):
        context = cast(dict[str, Any], super().get_serializer_context())
        timesheet_id = self.kwargs.get("timesheet_id")
        if timesheet_id:
            context["timesheet"] = get_object_or_404(
                WeeklyTimesheet, pk=timesheet_id, nanny=self.request.user)
        return context

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().filter(
            timesheet_id=kwargs["timesheet_id"])
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        timesheet = get_object_or_404(
            WeeklyTimesheet, pk=kwargs["timesheet_id"], nanny=request.user)
        ensure_timesheet_week_unlocked(timesheet)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(timesheet=timesheet)
        update_timesheet_status(timesheet)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        entry = self.get_object()
        ensure_timesheet_week_unlocked(entry.timesheet)
        serializer = self.get_serializer(
            entry, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        changed_fields = list(serializer.validated_data.keys())
        confirm_invalidate = _is_truthy(
            request.data.get("confirm_invalidate_signature"))
        if entry.signature_status == TimeEntry.SignatureStatus.SIGNED and changed_fields and not confirm_invalidate:
            return Response(
                {"detail": "Editing a signed entry requires confirm_invalidate_signature=true."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        invalidate_signature_if_needed(entry, changed_fields)
        update_timesheet_status(entry.timesheet)
        entry.refresh_from_db()
        return Response(self.get_serializer(entry).data)

    def destroy(self, request, *args, **kwargs):
        entry = self.get_object()
        ensure_timesheet_week_unlocked(entry.timesheet)
        timesheet = entry.timesheet
        entry.delete()
        update_timesheet_status(timesheet)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SignatureView(APIView):
    permission_classes = [IsNanny]

    def post(self, request, pk):
        entry = get_object_or_404(TimeEntry.objects.select_related(
            "timesheet", "timesheet__nanny"), pk=pk, timesheet__nanny=request.user)
        ensure_timesheet_week_unlocked(entry.timesheet)
        signature_value = request.data.get("image")
        if not signature_value or not str(signature_value).strip():
            return Response({"image": "Signature image is required."}, status=status.HTTP_400_BAD_REQUEST)
        if "," in signature_value:
            signature_value = signature_value.split(",", 1)[1]
        try:
            decoded = base64.b64decode(signature_value, validate=True)
        except (binascii.Error, ValueError):
            return Response({"image": "Invalid base64 image."}, status=status.HTTP_400_BAD_REQUEST)
        if not decoded:
            return Response({"image": "Signature image cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

        signature = replace_parent_signature_image(
            entry_id=entry.pk,
            image_name=f"signature_{entry.pk}.png",
            image_content=ContentFile(decoded),
            approved_snapshot={
                "entry_id": entry.pk,
                "work_date": entry.work_date.isoformat(),
                "family_name": entry.family_name,
                "family_requested_nanny": entry.family_requested_nanny,
                "start_time": entry.start_time.isoformat(),
                "end_time": entry.end_time.isoformat(),
                "total_hours": str(entry.total_hours),
                "notes": entry.notes,
            },
        )
        update_timesheet_status(signature.entry.timesheet)
        return Response(ParentSignatureSerializer(signature).data, status=status.HTTP_201_CREATED)


class AdminTimesheetViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsDashboardUser]

    def get_queryset(self):
        queryset = WeeklyTimesheet.objects.filter(submission__isnull=False).select_related(
            "nanny", "submission").prefetch_related(get_timesheet_entry_prefetch())
        request = cast(Request, self.request)
        return filter_submitted_timesheets(queryset, request.query_params)

    def get_serializer_class(self):
        if self.action in {"retrieve", "notes"}:
            return AdminTimesheetDetailSerializer
        return AdminTimesheetListSerializer

    @action(detail=True, methods=["get"], url_path="pdf")
    def pdf(self, request, pk=None):
        timesheet = self.get_object()
        if not timesheet.pdf_file:
            raise Http404("No PDF available for this timesheet.")
        return _pdf_file_response(timesheet)

    @action(detail=True, methods=["patch"], url_path="notes")
    def notes(self, request, pk=None):
        timesheet = self.get_object()
        serializer = AdminNotesUpdateSerializer(
            timesheet, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(AdminTimesheetDetailSerializer(timesheet).data)

    @action(detail=True, methods=["post"], url_path="override-submit")
    def override_submit(self, request, pk=None):
        timesheet = self.get_object()
        note = _clean_request_text(
            request.data.get("late_submission_note"),
            default="Admin override submission.",
        )
        timesheet = submit_timesheet(
            timesheet,
            submitted_by=request.user,
            force_late=True,
            late_submission_note=note,
        )
        return Response(AdminTimesheetDetailSerializer(timesheet).data)

    @action(detail=False, methods=["post"], url_path="weeks/lock")
    def lock_week(self, request):
        week_start = parse_date(str(request.data.get("week_start_date", "")))
        if not week_start:
            raise ValidationError(
                {"week_start_date": "A valid week_start_date is required."})
        note = _clean_request_text(request.data.get("note"))
        week_lock = lock_timesheet_week(week_start, locked_by=request.user, note=note)
        serializer = TimesheetWeekLockSerializer(week_lock)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
