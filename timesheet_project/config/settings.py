import sys
from datetime import timedelta
from pathlib import Path

from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent
IS_TESTING = "test" in sys.argv


def csv_config(name, default=""):
    return [value.strip() for value in str(config(name, default=default)).split(",") if value.strip()]


DEBUG = config("DEBUG", default=True, cast=bool)
SECRET_KEY = config("SECRET_KEY", default=None)
if not SECRET_KEY:
    if DEBUG or IS_TESTING:
        SECRET_KEY = "django-insecure-timesheetforyou-dev-key"
    else:
        raise ValueError("SECRET_KEY must be set when DEBUG is False.")

default_allowed_hosts = "*" if DEBUG else "testserver" if IS_TESTING else ""
ALLOWED_HOSTS = csv_config("ALLOWED_HOSTS", default=default_allowed_hosts)
if IS_TESTING and not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["testserver"]
if not DEBUG and not IS_TESTING:
    if not ALLOWED_HOSTS:
        raise ValueError("ALLOWED_HOSTS must be set when DEBUG is False.")
    if "*" in ALLOWED_HOSTS:
        raise ValueError("ALLOWED_HOSTS cannot include '*' when DEBUG is False.")

CSRF_TRUSTED_ORIGINS = csv_config("CSRF_TRUSTED_ORIGINS")
if not DEBUG and not IS_TESTING and not CSRF_TRUSTED_ORIGINS:
    raise ValueError("CSRF_TRUSTED_ORIGINS must be set when DEBUG is False.")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "django_filters",
    "accounts",
    "timesheets",
    "dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
]

USE_WHITENOISE = config("USE_WHITENOISE", default=not DEBUG, cast=bool)
if USE_WHITENOISE:
    MIDDLEWARE.append("whitenoise.middleware.WhiteNoiseMiddleware")

MIDDLEWARE += [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

if IS_TESTING:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "test_db.sqlite3",
        }
    }
else:
    database_name = config("POSTGRES_DB", default="") or config("DB_NAME", default="")
    if database_name:
        database_user = config("POSTGRES_USER", default="") or config("DB_USER", default="")
        database_password = config("POSTGRES_PASSWORD", default="") or config("DB_PASSWORD", default="")
        database_host = config("POSTGRES_HOST", default="") or config("DB_HOST", default="")

        if DEBUG:
            database_user = database_user or "postgres"
            database_password = database_password or "postgres"
            database_host = database_host or "localhost"
        else:
            missing_database_settings = []
            if not database_user:
                missing_database_settings.append("POSTGRES_USER or DB_USER")
            if not database_password:
                missing_database_settings.append("POSTGRES_PASSWORD or DB_PASSWORD")
            if not database_host:
                missing_database_settings.append("POSTGRES_HOST or DB_HOST")
            if missing_database_settings:
                raise ValueError(
                    "Production PostgreSQL configuration is incomplete; missing "
                    + ", ".join(missing_database_settings)
                    + "."
                )

        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": database_name,
                "USER": database_user,
                "PASSWORD": database_password,
                "HOST": database_host,
                "PORT": config("POSTGRES_PORT", default=config("DB_PORT", default="5432")),
                "CONN_MAX_AGE": config("DB_CONN_MAX_AGE", default=60, cast=int),
            }
        }
        if config("DB_SSL_REQUIRE", default=False, cast=bool):
            DATABASES["default"]["OPTIONS"] = {"sslmode": "require"}
    elif not DEBUG:
        raise ValueError("POSTGRES_DB or DB_NAME must be set when DEBUG is False.")
    else:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / "db.sqlite3",
            }
        }

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
USE_S3 = config("USE_S3", default=False, cast=bool)

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        if USE_WHITENOISE
        else "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

if USE_S3:
    AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", default="us-east-1")
    AWS_LOCATION = config("AWS_LOCATION", default="media")
    AWS_QUERYSTRING_AUTH = config("AWS_QUERYSTRING_AUTH", default=True, cast=bool)
    AWS_QUERYSTRING_EXPIRE = config("AWS_QUERYSTRING_EXPIRE", default=3600, cast=int)
    AWS_S3_FILE_OVERWRITE = config("AWS_S3_FILE_OVERWRITE", default=False, cast=bool)
    AWS_DEFAULT_ACL = None
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": config("AWS_S3_CACHE_CONTROL", default="private, max-age=300"),
    }

    MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/{AWS_LOCATION}/"
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
            "region_name": AWS_S3_REGION_NAME,
            "location": AWS_LOCATION,
            "default_acl": AWS_DEFAULT_ACL,
            "querystring_auth": AWS_QUERYSTRING_AUTH,
            "querystring_expire": AWS_QUERYSTRING_EXPIRE,
            "file_overwrite": AWS_S3_FILE_OVERWRITE,
            "object_parameters": AWS_S3_OBJECT_PARAMETERS,
        },
    }

USE_SNS = config("USE_SNS", default=False, cast=bool)
AWS_SNS_REGION_NAME = config("AWS_SNS_REGION_NAME", default=config("AWS_REGION", default=""))
SNS_SENDER_ID = config("SNS_SENDER_ID", default="")

DEFAULT_EMAIL_BACKEND = (
    "django.core.mail.backends.console.EmailBackend"
    if DEBUG or IS_TESTING
    else "django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_BACKEND = config("EMAIL_BACKEND", default=DEFAULT_EMAIL_BACKEND)
EMAIL_HOST = config("EMAIL_HOST", default="")
if (
    not DEBUG
    and not IS_TESTING
    and EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend"
    and not EMAIL_HOST
):
    raise ValueError("EMAIL_HOST must be set when DEBUG is False and EMAIL_BACKEND uses SMTP.")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="no-reply@timesheetforyou.local")
SITE_BASE_URL = config("SITE_BASE_URL", default="http://localhost:8000")
ACCOUNT_SETUP_BASE_URL = config("ACCOUNT_SETUP_BASE_URL", default=SITE_BASE_URL)
ACCOUNT_SETUP_TOKEN_DAYS = config("ACCOUNT_SETUP_TOKEN_DAYS", default=7, cast=int)
ADMIN_NOTIFICATION_EMAIL = config("ADMIN_NOTIFICATION_EMAIL", default="")

SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=not DEBUG and not IS_TESTING, cast=bool)
SECURE_REDIRECT_EXEMPT = csv_config("SECURE_REDIRECT_EXEMPT", default="^/?healthz/$")
SECURE_PROXY_SSL_HEADER = (
    ("HTTP_X_FORWARDED_PROTO", "https")
    if config("USE_X_FORWARDED_PROTO", default=False, cast=bool)
    else None
)
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=not DEBUG, cast=bool)
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=not DEBUG, cast=bool)
SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=0, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False, cast=bool)
SECURE_HSTS_PRELOAD = config("SECURE_HSTS_PRELOAD", default=False, cast=bool)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = config("SECURE_REFERRER_POLICY", default="same-origin")
X_FRAME_OPTIONS = "DENY"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}
