import base64
from datetime import date, time, timedelta
from io import BytesIO
from pathlib import Path
import shutil

from PIL import Image
from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from timesheets.admin import ParentSignatureAdmin
from timesheets.models import ParentSignature, TimeEntry, WeeklyTimesheet
from timesheets.services import calculate_total_hours


TEST_MEDIA_ROOT = Path(settings.BASE_DIR) / "test_media_signature_storage"


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ParentSignatureStorageTests(APITestCase):
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
        )
        self.admin = User.objects.create_superuser(
            username="admin1",
            password="StrongTestPass123!",
            email="admin@example.com",
        )
        self.week_start = date(2026, 7, 11)
        self.timesheet = WeeklyTimesheet.objects.create(
            nanny=self.nanny,
            week_start_date=self.week_start,
            week_end_date=self.week_start + timedelta(days=6),
        )
        self.entry = TimeEntry.objects.create(
            timesheet=self.timesheet,
            work_date=self.week_start,
            family_name="Smith",
            start_time=time(9, 0),
            end_time=time(17, 0),
            total_hours=calculate_total_hours(time(9, 0), time(17, 0)),
        )

    def signature_bytes(self, color):
        image = Image.new("RGB", (20, 20), color=color)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    def uploaded_signature(self, color, filename="admin_signature.png"):
        return SimpleUploadedFile(
            filename,
            self.signature_bytes(color),
            content_type="image/png",
        )

    def signature_base64(self, color):
        return base64.b64encode(self.signature_bytes(color)).decode("utf-8")

    def post_api_signature(self, color):
        self.client.force_authenticate(user=self.nanny)
        return self.client.post(
            reverse("entry-signature", args=[self.entry.pk]),
            {"image": self.signature_base64(color)},
            format="json",
        )

    def login_admin(self):
        self.client.force_authenticate(user=None)
        self.client.force_login(self.admin)

    def test_api_replacing_parent_signature_deletes_previous_file(self):
        first_response = self.post_api_signature("black")
        signature = ParentSignature.objects.get(entry=self.entry)
        old_image_name = signature.image.name
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(signature.image.storage.exists(old_image_name))

        with self.captureOnCommitCallbacks(execute=True):
            second_response = self.post_api_signature("white")
        signature.refresh_from_db()

        self.assertEqual(second_response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(signature.image.name, old_image_name)
        self.assertFalse(signature.image.storage.exists(old_image_name))
        self.assertTrue(signature.image.storage.exists(signature.image.name))

    def test_admin_creating_parent_signature_updates_timesheet_status(self):
        self.login_admin()

        response = self.client.post(
            reverse("admin:timesheets_parentsignature_add"),
            {
                "entry": self.entry.pk,
                "image": self.uploaded_signature("black"),
                "approved_snapshot": "{}",
                "_save": "Save",
            },
        )
        self.timesheet.refresh_from_db()
        self.entry.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.entry.signature_status, TimeEntry.SignatureStatus.SIGNED)
        self.assertEqual(self.timesheet.status, WeeklyTimesheet.Status.FULLY_SIGNED)

    def test_admin_replacing_parent_signature_uses_shared_cleanup(self):
        self.post_api_signature("black")
        signature = ParentSignature.objects.get(entry=self.entry)
        old_image_name = signature.image.name
        self.assertTrue(signature.image.storage.exists(old_image_name))

        self.login_admin()
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("admin:timesheets_parentsignature_change", args=[signature.pk]),
                {
                    "image": self.uploaded_signature("white"),
                    "approved_snapshot": "{}",
                    "_save": "Save",
                },
            )
        signature.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(signature.image.name, old_image_name)
        self.assertFalse(signature.image.storage.exists(old_image_name))
        self.assertTrue(signature.image.storage.exists(signature.image.name))

    def test_parent_signature_admin_makes_entry_readonly_on_existing_rows(self):
        self.post_api_signature("black")
        signature = ParentSignature.objects.get(entry=self.entry)
        model_admin = ParentSignatureAdmin(ParentSignature, AdminSite())

        self.assertIn("entry", model_admin.get_readonly_fields(request=None, obj=signature))
