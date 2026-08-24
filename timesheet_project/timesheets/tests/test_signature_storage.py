import base64
from datetime import date, time, timedelta
from io import BytesIO
from pathlib import Path
import shutil

from PIL import Image
from django.conf import settings
from django.urls import reverse
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
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

    def signature_base64(self, color):
        image = Image.new("RGB", (20, 20), color=color)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def test_api_replacing_parent_signature_deletes_previous_file(self):
        self.client.force_authenticate(user=self.nanny)
        url = reverse("entry-signature", args=[self.entry.pk])

        first_response = self.client.post(
            url,
            {"image": self.signature_base64("black")},
            format="json",
        )
        signature = ParentSignature.objects.get(entry=self.entry)
        old_image_name = signature.image.name
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(signature.image.storage.exists(old_image_name))

        second_response = self.client.post(
            url,
            {"image": self.signature_base64("white")},
            format="json",
        )
        signature.refresh_from_db()

        self.assertEqual(second_response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(signature.image.name, old_image_name)
        self.assertFalse(signature.image.storage.exists(old_image_name))
        self.assertTrue(signature.image.storage.exists(signature.image.name))
