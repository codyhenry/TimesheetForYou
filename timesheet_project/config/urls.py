from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts import setup_views
from . import views

handler404 = "config.views.custom_404"

urlpatterns = [
    path("", views.root_redirect, name="root-redirect"),
    path("healthz/", views.healthz, name="healthz"),
    path("account-setup/", setup_views.account_setup, name="account-setup-web"),
    path("django-admin/", admin.site.urls),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/", include("accounts.urls")),
    path("api/", include("timesheets.urls")),
    path("dashboard/", include("dashboard.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
