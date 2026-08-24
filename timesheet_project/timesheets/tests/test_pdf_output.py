import base64
import shutil
from datetime import date, time, timedelta
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from django.conf import settings
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings

from accounts.models import User
from timesheets.models import ParentSignature, TimeEntry, WeeklyTimesheet
from timesheets.services import (
    calculate_total_hours,
    format_timesheet_pdf_filename,
    submit_timesheet,
)


TEST_MEDIA_ROOT = Path(settings.BASE_DIR) / "test_media_pdf_output"


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class TimesheetPDFOutputTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        if TEST_MEDIA_ROOT.exists():
            shutil.rmtree(TEST_MEDIA_ROOT)

    def setUp(self):
        self.nanny = User.objects.create_user(
            username="nanny1",
            password="StrongTestPass123!",
            role=User.Role.NANNY,
            first_name="John",
            last_name="Doe",
        )
        self.week_start = date(2026, 7, 11)
        self.timesheet = WeeklyTimesheet.objects.create(
            nanny=self.nanny,
            week_start_date=self.week_start,
            week_end_date=self.week_start + timedelta(days=6),
        )

    def create_entry(self, *, family_requested_nanny=False, notes=""):
        return TimeEntry.objects.create(
            timesheet=self.timesheet,
            work_date=self.week_start,
            family_name="Smith",
            family_requested_nanny=family_requested_nanny,
            start_time=time(9, 0),
            end_time=time(17, 0),
            total_hours=calculate_total_hours(time(9, 0), time(17, 0)),
            notes=notes,
        )

    def signature_content_file(self, color="black"):
        image = Image.new("RGB", (20, 20), color=color)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return ContentFile(buffer.getvalue(), name="signature.png")

    def test_pdf_filename_uses_nanny_name_and_week_range(self):
        self.assertEqual(
            format_timesheet_pdf_filename(self.timesheet),
            "Doe,John 7.11.26-7.17.26.pdf",
        )

    def test_submission_uses_display_pdf_filename_for_timesheet_and_submission(self):
        self.create_entry(
            family_requested_nanny=True,
            notes="Parent asked for extra pickup notes.",
        )

        submit_timesheet(self.timesheet)
        self.timesheet.refresh_from_db()

        assert self.timesheet.submission is not None
        self.assertTrue(self.timesheet.pdf_file.name.endswith("Doe,John 7.11.26-7.17.26.pdf"))
        self.assertTrue(
            self.timesheet.submission.pdf_file.name.endswith(
                "Doe,John 7.11.26-7.17.26.pdf"
            )
        )
        with self.timesheet.pdf_file.open("rb") as pdf_file:
            self.assertTrue(pdf_file.read().startswith(b"%PDF"))

    def test_signed_signature_pdf_rendering_does_not_require_local_path(self):
        entry = self.create_entry()
        signature = ParentSignature(entry=entry)
        signature.image.save("signature.png", self.signature_content_file(), save=True)
        entry.signature_status = TimeEntry.SignatureStatus.SIGNED
        entry.save(update_fields=["signature_status", "updated_at"])

        with patch.object(type(signature.image), "path", new_callable=property, side_effect=NotImplementedError):
            submit_timesheet(self.timesheet)

        self.timesheet.refresh_from_db()
        with self.timesheet.pdf_file.open("rb") as pdf_file:
            self.assertTrue(pdf_file.read().startswith(b"%PDF"))
