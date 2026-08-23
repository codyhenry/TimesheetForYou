import json
import os
import subprocess
import sys

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

    @override_settings(SECURE_SSL_REDIRECT=True, SECURE_REDIRECT_EXEMPT=["^/?healthz/$"])
    def test_healthz_returns_ok_without_authentication_when_ssl_redirects_are_enabled(self):
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
    def _load_settings_subprocess(self, extra_env, argv_suffix=None):
        env = os.environ.copy()
        env.update(extra_env)
        env["PYTHONPATH"] = str(settings.BASE_DIR)
        code = """
import json
import config.settings as s
print(json.dumps({
    "allowed_hosts": s.ALLOWED_HOSTS,
    "csrf_trusted_origins": s.CSRF_TRUSTED_ORIGINS,
    "database_engine": s.DATABASES["default"]["ENGINE"],
    "database_name": str(s.DATABASES["default"]["NAME"]),
    "database_user": s.DATABASES["default"].get("USER"),
    "database_password": s.DATABASES["default"].get("PASSWORD"),
    "database_host": s.DATABASES["default"].get("HOST"),
    "database_conn_max_age": s.DATABASES["default"].get("CONN_MAX_AGE"),
    "database_options": s.DATABASES["default"].get("OPTIONS", {}),
    "use_whitenoise": s.USE_WHITENOISE,
    "middleware": s.MIDDLEWARE,
    "staticfiles_backend": s.STORAGES["staticfiles"]["BACKEND"],
    "secure_ssl_redirect": s.SECURE_SSL_REDIRECT,
    "secure_redirect_exempt": s.SECURE_REDIRECT_EXEMPT,
    "secure_proxy_ssl_header": s.SECURE_PROXY_SSL_HEADER,
    "session_cookie_secure": s.SESSION_COOKIE_SECURE,
    "csrf_cookie_secure": s.CSRF_COOKIE_SECURE,
    "secure_hsts_seconds": s.SECURE_HSTS_SECONDS,
    "secure_content_type_nosniff": s.SECURE_CONTENT_TYPE_NOSNIFF,
    "secure_referrer_policy": s.SECURE_REFERRER_POLICY,
    "x_frame_options": s.X_FRAME_OPTIONS,
}))
"""
        command = [sys.executable, "-c", code]
        if argv_suffix:
            command.extend(argv_suffix)
        return subprocess.run(
            command,
            cwd=settings.BASE_DIR,
            env=env,
            capture_output=True,
            text=True,
        )

    def _production_env(self, **overrides):
        env = {
            "DEBUG": "False",
            "SECRET_KEY": "production-test-secret",
            "ALLOWED_HOSTS": "timesheet.example.com,www.timesheet.example.com",
            "CSRF_TRUSTED_ORIGINS": "https://timesheet.example.com,https://www.timesheet.example.com",
            "POSTGRES_DB": "timesheet_for_you",
            "POSTGRES_USER": "timesheet_user",
            "POSTGRES_PASSWORD": "timesheet_password",
            "POSTGRES_HOST": "db.example.com",
            "POSTGRES_PORT": "5432",
        }
        env.update(overrides)
        return env

    def test_csv_config_strips_empty_values(self):
        self.assertEqual(
            csv_config("TEST_CSV_SETTING", default=" one.example.com, two.example.com ,, "),
            ["one.example.com", "two.example.com"],
        )

    def test_production_settings_load_from_environment(self):
        result = self._load_settings_subprocess(
            self._production_env(
                DB_CONN_MAX_AGE="120",
                DB_SSL_REQUIRE="True",
                USE_WHITENOISE="True",
                SECURE_SSL_REDIRECT="True",
                SESSION_COOKIE_SECURE="True",
                CSRF_COOKIE_SECURE="True",
                SECURE_HSTS_SECONDS="31536000",
            )
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        loaded = json.loads(result.stdout)
        self.assertEqual(
            loaded["allowed_hosts"],
            ["timesheet.example.com", "www.timesheet.example.com"],
        )
        self.assertEqual(
            loaded["csrf_trusted_origins"],
            ["https://timesheet.example.com", "https://www.timesheet.example.com"],
        )
        self.assertEqual(loaded["database_engine"], "django.db.backends.postgresql")
        self.assertEqual(loaded["database_name"], "timesheet_for_you")
        self.assertEqual(loaded["database_user"], "timesheet_user")
        self.assertEqual(loaded["database_password"], "timesheet_password")
        self.assertEqual(loaded["database_host"], "db.example.com")
        self.assertEqual(loaded["database_conn_max_age"], 120)
        self.assertEqual(loaded["database_options"], {"sslmode": "require"})
        self.assertTrue(loaded["use_whitenoise"])
        self.assertIn("whitenoise.middleware.WhiteNoiseMiddleware", loaded["middleware"])
        self.assertEqual(
            loaded["staticfiles_backend"],
            "whitenoise.storage.CompressedManifestStaticFilesStorage",
        )
        self.assertTrue(loaded["secure_ssl_redirect"])
        self.assertEqual(loaded["secure_redirect_exempt"], ["^/?healthz/$"])
        self.assertIsNone(loaded["secure_proxy_ssl_header"])
        self.assertTrue(loaded["session_cookie_secure"])
        self.assertTrue(loaded["csrf_cookie_secure"])
        self.assertEqual(loaded["secure_hsts_seconds"], 31536000)
        self.assertTrue(loaded["secure_content_type_nosniff"])
        self.assertEqual(loaded["secure_referrer_policy"], "same-origin")
        self.assertEqual(loaded["x_frame_options"], "DENY")

    def test_forwarded_proto_trust_is_explicit_opt_in(self):
        result = self._load_settings_subprocess(
            self._production_env(USE_X_FORWARDED_PROTO="True")
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        loaded = json.loads(result.stdout)
        self.assertEqual(loaded["secure_proxy_ssl_header"], ["HTTP_X_FORWARDED_PROTO", "https"])

    def test_production_rejects_wildcard_allowed_hosts(self):
        result = self._load_settings_subprocess(
            self._production_env(ALLOWED_HOSTS="*")
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ALLOWED_HOSTS cannot include '*'", result.stderr)

    def test_production_requires_csrf_trusted_origins(self):
        result = self._load_settings_subprocess(
            self._production_env(CSRF_TRUSTED_ORIGINS="")
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CSRF_TRUSTED_ORIGINS must be set", result.stderr)

    def test_test_mode_allows_debug_false_without_production_hosts(self):
        result = self._load_settings_subprocess(
            {
                "DEBUG": "False",
                "SECRET_KEY": "",
                "ALLOWED_HOSTS": "",
                "CSRF_TRUSTED_ORIGINS": "",
            },
            argv_suffix=["manage.py", "test"],
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        loaded = json.loads(result.stdout)
        self.assertEqual(loaded["allowed_hosts"], ["testserver"])
        self.assertEqual(loaded["database_engine"], "django.db.backends.sqlite3")
        self.assertTrue(loaded["database_name"].endswith("test_db.sqlite3"))
        self.assertFalse(loaded["secure_ssl_redirect"])

    def test_production_uses_db_name_when_postgres_db_is_empty(self):
        result = self._load_settings_subprocess(
            self._production_env(POSTGRES_DB="", DB_NAME="legacy_timesheet_for_you")
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        loaded = json.loads(result.stdout)
        self.assertEqual(loaded["database_name"], "legacy_timesheet_for_you")

    def test_production_requires_database_name(self):
        result = self._load_settings_subprocess(
            self._production_env(POSTGRES_DB="", DB_NAME="")
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("POSTGRES_DB or DB_NAME must be set", result.stderr)

    def test_production_requires_database_connection_fields(self):
        result = self._load_settings_subprocess(
            self._production_env(
                POSTGRES_USER="",
                DB_USER="",
                POSTGRES_PASSWORD="",
                DB_PASSWORD="",
                POSTGRES_HOST="",
                DB_HOST="",
            )
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Production PostgreSQL configuration is incomplete", result.stderr)
        self.assertIn("POSTGRES_USER or DB_USER", result.stderr)
        self.assertIn("POSTGRES_PASSWORD or DB_PASSWORD", result.stderr)
        self.assertIn("POSTGRES_HOST or DB_HOST", result.stderr)

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
