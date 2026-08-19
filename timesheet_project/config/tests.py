from django.conf import settings
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse


@override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"])
class RootAndErrorRoutingTests(TestCase):
    def test_root_redirects_to_dashboard(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("dashboard-index"))

    def test_browser_unknown_route_uses_themed_404(self):
        response = self.client.get("/not-a-real-browser-page/")

        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "This page wandered off during nap time.", status_code=404)
        self.assertContains(response, "Go to Dashboard", status_code=404)
        self.assertContains(response, reverse("dashboard-index"), status_code=404)

    def test_api_unknown_route_returns_json_404(self):
        response = self.client.get("/api/not-a-real-endpoint/")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json(), {"detail": "Not found."})


class MediaStorageSettingsTests(SimpleTestCase):
    def test_filesystem_storage_is_default_for_local_and_test_runs(self):
        self.assertFalse(settings.USE_S3)
        self.assertEqual(settings.MEDIA_URL, "/media/")
        self.assertEqual(
            settings.STORAGES["default"]["BACKEND"],
            "django.core.files.storage.FileSystemStorage",
        )

    @override_settings(
        USE_S3=True,
        AWS_STORAGE_BUCKET_NAME="example-media-bucket",
        AWS_S3_REGION_NAME="us-east-2",
        AWS_LOCATION="private-media",
        STORAGES={
            "default": {
                "BACKEND": "storages.backends.s3.S3Storage",
                "OPTIONS": {
                    "bucket_name": "example-media-bucket",
                    "region_name": "us-east-2",
                    "location": "private-media",
                    "querystring_auth": True,
                    "querystring_expire": 3600,
                    "file_overwrite": False,
                },
            },
            "staticfiles": {
                "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
            },
        },
    )
    def test_s3_storage_settings_are_private_and_non_overwriting(self):
        storage_options = settings.STORAGES["default"]["OPTIONS"]

        self.assertTrue(settings.USE_S3)
        self.assertEqual(settings.STORAGES["default"]["BACKEND"], "storages.backends.s3.S3Storage")
        self.assertEqual(storage_options["bucket_name"], "example-media-bucket")
        self.assertEqual(storage_options["location"], "private-media")
        self.assertTrue(storage_options["querystring_auth"])
        self.assertEqual(storage_options["querystring_expire"], 3600)
        self.assertFalse(storage_options["file_overwrite"])
