from django.urls import path

from .views import (
    AccountSetupCompleteView,
    AccountSetupRequestView,
    AccountSetupValidateView,
    ChangePasswordView,
    CurrentUserView,
    DashboardUserManagementViewSet,
    NannyManagementViewSet,
)

nanny_list = NannyManagementViewSet.as_view({"get": "list", "post": "create"})
nanny_detail = NannyManagementViewSet.as_view({"patch": "partial_update"})
dashboard_user_list = DashboardUserManagementViewSet.as_view({"get": "list", "post": "create"})
dashboard_user_detail = DashboardUserManagementViewSet.as_view({"patch": "partial_update"})

urlpatterns = [
    path("auth/me/", CurrentUserView.as_view(), name="current-user"),
    path("auth/password/", ChangePasswordView.as_view(), name="change-password"),
    path("auth/account-setup/request/", AccountSetupRequestView.as_view(), name="account-setup-request"),
    path("auth/account-setup/validate/", AccountSetupValidateView.as_view(), name="account-setup-validate"),
    path("auth/account-setup/complete/", AccountSetupCompleteView.as_view(), name="account-setup-complete"),
    path("admin/nannies/", nanny_list, name="admin-nanny-list"),
    path("admin/nannies/<int:pk>/", nanny_detail, name="admin-nanny-detail"),
    path("admin/dashboard-users/", dashboard_user_list, name="admin-dashboard-user-list"),
    path("admin/dashboard-users/<int:pk>/", dashboard_user_detail, name="admin-dashboard-user-detail"),
]
