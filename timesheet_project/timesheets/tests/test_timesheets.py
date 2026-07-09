import base64
import io
import shutil
from datetime import time, timedelta
from pathlib import Path
from typing import Any

from PIL import Image
from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from timesheets.models import ParentSignature, TimeEntry, WeeklyTimesheet
from timesheets.services import calculate_total_hours, submit_timesheet

TEST_MEDIA_ROOT = Path(settings.BASE_DIR) / "test_media"


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class TimesheetAPITests(APITestCase):
    client: Any

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        if TEST_MEDIA_ROOT.exists():
            shutil.rmtree(TEST_MEDIA_ROOT)

    def setUp(self):
        self.nanny = User.objects.create_user(
            username="nanny1",
            password='StrongTestPass123!',
            role=User.Role.NANNY,
            first_name="Nina",
            last_name="Nanny",
        )
        self.other_nanny = User.objects.create_user(
            username="nanny2",
            password='StrongTestPass123!',
            role=User.Role.NANNY,
        )
        self.admin = User.objects.create_user(
            username="admin1",
            password='StrongTestPass123!',
            role=User.Role.ADMIN,
            is_staff=True,
        )
        self.week_start = timezone.localdate() - timedelta(days=timezone.localdate().weekday())
        self.week_end = self.week_start + timedelta(days=6)

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def make_signature_base64(self):
        image = Image.new("RGB", (20, 20), color="black")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def create_timesheet(self, user=None):
        return WeeklyTimesheet.objects.create(
            nanny=user or self.nanny,
            week_start_date=self.week_start,
            week_end_date=self.week_end,
        )

    def create_entry(self, timesheet, signed=False, work_date=None, family_name="Smith", start_time=time(9, 0), end_time=time(17, 0)):
        entry = TimeEntry.objects.create(
            timesheet=timesheet,
            work_date=work_date or timesheet.week_start_date,
            family_name=family_name,
            start_time=start_time,
            end_time=end_time,
            total_hours=calculate_total_hours(start_time, end_time),
        )
        if signed:
            signature = ParentSignature(
                entry=entry,
                approved_snapshot={
                    "family_name": entry.family_name,
                    "work_date": entry.work_date.isoformat(),
                },
            )
            signature.image.save("seed_signature.png",
                                 self._signature_content_file(), save=True)
            entry.signature_status = TimeEntry.SignatureStatus.SIGNED
            entry.save(update_fields=["signature_status", "updated_at"])
        return entry

    def _signature_content_file(self):
        from django.core.files.base import ContentFile
        return ContentFile(base64.b64decode(self.make_signature_base64()), name="signature.png")

    def submit_existing_timesheet(self, timesheet):
        return submit_timesheet(timesheet)

    def test_nanny_can_get_create_current_week_timesheet(self):
        self.authenticate(self.nanny)
        url = reverse("timesheet-current")

        first_response = self.client.get(url)
        second_response = self.client.get(url)

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertEqual(WeeklyTimesheet.objects.filter(
            nanny=self.nanny).count(), 1)

    def test_nanny_cannot_access_another_nannys_timesheet(self):
        self.authenticate(self.nanny)
        other_timesheet = self.create_timesheet(user=self.other_nanny)

        response = self.client.get(
            reverse("timesheet-detail", args=[other_timesheet.pk]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_view_submitted_timesheets(self):
        timesheet = self.create_timesheet()
        self.create_entry(timesheet)
        self.submit_existing_timesheet(timesheet)
        self.authenticate(self.admin)

        response = self.client.get(reverse("admin-timesheet-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], timesheet.pk)

    def test_time_entry_total_hours_are_calculated_correctly(self):
        self.authenticate(self.nanny)
        timesheet = self.create_timesheet()

        response = self.client.post(
            reverse("entry-list-create", args=[timesheet.pk]),
            {
                "work_date": str(self.week_start),
                "family_name": "Smith",
                "start_time": "09:00:00",
                "end_time": "17:30:00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(response.data["total_hours"]), "8.50")

    def test_end_time_before_start_time_is_rejected(self):
        self.authenticate(self.nanny)
        timesheet = self.create_timesheet()

        response = self.client.post(
            reverse("entry-list-create", args=[timesheet.pk]),
            {
                "work_date": str(self.week_start),
                "family_name": "Smith",
                "start_time": "17:00:00",
                "end_time": "09:00:00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("end_time", response.data)

    def test_date_outside_timesheet_week_is_rejected(self):
        self.authenticate(self.nanny)
        timesheet = self.create_timesheet()

        response = self.client.post(
            reverse("entry-list-create", args=[timesheet.pk]),
            {
                "work_date": str(self.week_end + timedelta(days=1)),
                "family_name": "Smith",
                "start_time": "09:00:00",
                "end_time": "17:00:00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("work_date", response.data)

    def test_signed_entry_edit_without_confirmation_is_rejected(self):
        self.authenticate(self.nanny)
        timesheet = self.create_timesheet()
        entry = self.create_entry(timesheet, signed=True)

        response = self.client.patch(
            reverse("entry-detail", args=[entry.pk]),
            {"family_name": "Johnson"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_signed_entry_edit_with_confirmation_invalidates_signature(self):
        self.authenticate(self.nanny)
        timesheet = self.create_timesheet()
        entry = self.create_entry(timesheet, signed=True)

        response = self.client.patch(
            reverse("entry-detail", args=[entry.pk]),
            {"family_name": "Johnson", "confirm_invalidate_signature": True},
            format="json",
        )
        entry.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(entry.signature_status,
                         TimeEntry.SignatureStatus.SIGNATURE_INVALIDATED)

    def test_parent_signature_creates_approved_snapshot(self):
        self.authenticate(self.nanny)
        timesheet = self.create_timesheet()
        entry = self.create_entry(timesheet)

        response = self.client.post(
            reverse("entry-signature", args=[entry.pk]),
            {"image": self.make_signature_base64()},
            format="json",
        )
        entry.refresh_from_db()
        signature = ParentSignature.objects.get(entry=entry)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(entry.signature_status,
                         TimeEntry.SignatureStatus.SIGNED)
        self.assertEqual(
            signature.approved_snapshot["family_name"], entry.family_name)

    def test_signature_cannot_be_added_after_submission(self):
        self.authenticate(self.nanny)
        timesheet = self.create_timesheet()
        entry = self.create_entry(timesheet)
        self.client.post(reverse("timesheet-submit", args=[timesheet.pk]))

        response = self.client.post(
            reverse("entry-signature", args=[entry.pk]),
            {"image": self.make_signature_base64()},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submission_allowed_with_unsigned_entries(self):
        self.authenticate(self.nanny)
        timesheet = self.create_timesheet()
        self.create_entry(timesheet)

        response = self.client.post(
            reverse("timesheet-submit", args=[timesheet.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["status"], WeeklyTimesheet.Status.SUBMITTED_WITH_UNSIGNED_ENTRIES)

    def test_submission_status_is_submitted_with_unsigned_entries_when_unsigned_entries_exist(self):
        self.authenticate(self.nanny)
        timesheet = self.create_timesheet()
        self.create_entry(timesheet, signed=True)
        self.create_entry(timesheet, family_name="Jones")

        response = self.client.post(
            reverse("timesheet-submit", args=[timesheet.pk]))
        timesheet.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            timesheet.status, WeeklyTimesheet.Status.SUBMITTED_WITH_UNSIGNED_ENTRIES)

    def test_submission_status_is_submitted_fully_signed_when_all_entries_are_signed(self):
        self.authenticate(self.nanny)
        timesheet = self.create_timesheet()
        self.create_entry(timesheet, signed=True)
        self.create_entry(timesheet, signed=True, family_name="Jones")

        response = self.client.post(
            reverse("timesheet-submit", args=[timesheet.pk]))
        timesheet.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(timesheet.status,
                         WeeklyTimesheet.Status.SUBMITTED_FULLY_SIGNED)

    def test_pdf_is_generated_on_submission(self):
        self.authenticate(self.nanny)
        timesheet = self.create_timesheet()
        self.create_entry(timesheet)

        response = self.client.post(
            reverse("timesheet-submit", args=[timesheet.pk]))
        timesheet.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(timesheet.pdf_file.name)
        self.assertIsNotNone(timesheet.submission)
        assert timesheet.submission is not None
        self.assertTrue(timesheet.submission.pdf_file.name)
        with timesheet.pdf_file.open("rb") as pdf_file:
            self.assertTrue(pdf_file.read().startswith(b"%PDF"))

    def test_submitted_timesheet_cannot_be_edited(self):
        self.authenticate(self.nanny)
        timesheet = self.create_timesheet()
        entry = self.create_entry(timesheet)
        self.client.post(reverse("timesheet-submit", args=[timesheet.pk]))

        patch_response = self.client.patch(reverse(
            "entry-detail", args=[entry.pk]), {"family_name": "Edited"}, format="json")
        create_response = self.client.post(
            reverse("entry-list-create", args=[timesheet.pk]),
            {
                "work_date": str(self.week_start),
                "family_name": "Late Family",
                "start_time": "09:00:00",
                "end_time": "11:00:00",
            },
            format="json",
        )

        self.assertEqual(patch_response.status_code,
                         status.HTTP_400_BAD_REQUEST)
        self.assertEqual(create_response.status_code,
                         status.HTTP_400_BAD_REQUEST)

    def test_admin_can_update_admin_notes_after_submission(self):
        timesheet = self.create_timesheet()
        self.create_entry(timesheet)
        self.submit_existing_timesheet(timesheet)
        self.authenticate(self.admin)

        response = self.client.patch(
            reverse("admin-timesheet-notes", args=[timesheet.pk]),
            {"admin_notes": "Reviewed and approved."},
            format="json",
        )
        timesheet.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(timesheet.admin_notes, "Reviewed and approved.")

    def test_nanny_cannot_update_admin_notes(self):
        timesheet = self.create_timesheet()
        self.create_entry(timesheet)
        self.submit_existing_timesheet(timesheet)
        self.authenticate(self.nanny)

        response = self.client.patch(
            reverse("admin-timesheet-notes", args=[timesheet.pk]),
            {"admin_notes": "Not allowed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
