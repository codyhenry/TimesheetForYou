from django.conf import settings
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from config import views
from config.settings import csv_config


@override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"])
class RootAndErrorRoutingTests(TestCase):
    def test_root_redirects_to_dashboard(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("dashboard-index"))

    def test_healthz_returns_ok_without_authentication(self):
        response = self.client.get(reverse("healthz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

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


class ProductionSettingsHelpersTests(SimpleTestCase):
    def test_csv_config_strips_empty_values(self):
        self.assertEqual(
            csv_config("TEST_CSV_SETTING", default=" one.example.com, two.example.com ,, "),
            ["one.example.com", "two.example.com"],
        )

    @override_settings(
        DEBUG=False,
        USE_WHITENOISE=True,
        MIDDLEWARE=[
            "django.middleware.security.SecurityMiddleware",
            "whitenoise.middleware.WhiteNoiseMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
        ],
        STORAGES={
            "default": {
                "BACKEND": "django.core.files.storage.FileSystemStorage",
            },
            "staticfiles": {
                "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
            },
        },
        SECURE_SSL_REDIRECT=True,
        SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO", "https"),
        SESSION_COOKIE_SECURE=True,
        CSRF_COOKIE_SECURE=True,
        SECURE_HSTS_SECONDS=31536000,
        SECURE_CONTENT_TYPE_NOSNIFF=True,
        SECURE_REFERRER_POLICY="same-origin",
        X_FRAME_OPTIONS="DENY",
    )
    def test_production_security_and_static_settings(self):
        self.assertIn("whitenoise.middleware.WhiteNoiseMiddleware", settings.MIDDLEWARE)
        self.assertEqual(
            settings.STORAGES["staticfiles"]["BACKEND"],
            "whitenoise.storage.CompressedManifestStaticFilesStorage",
        )
        self.assertTrue(settings.SECURE_SSL_REDIRECT)
        self.assertEqual(settings.SECURE_PROXY_SSL_HEADER, ("HTTP_X_FORWARDED_PROTO", "https"))
        self.assertTrue(settings.SESSION_COOKIE_SECURE)
        self.assertTrue(settings.CSRF_COOKIE_SECURE)
        self.assertEqual(settings.SECURE_HSTS_SECONDS, 31536000)
        self.assertTrue(settings.SECURE_CONTENT_TYPE_NOSNIFF)
        self.assertEqual(settings.SECURE_REFERRER_POLICY, "same-origin")
        self.assertEqual(settings.X_FRAME_OPTIONS, "DENY")

    def test_health_view_response_shape(self):
        response = views.healthz(None)

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "ok"})


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
