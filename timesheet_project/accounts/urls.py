from django.urls import path

from .views import CurrentUserView, NannyManagementViewSet

nanny_list = NannyManagementViewSet.as_view({"get": "list", "post": "create"})
nanny_detail = NannyManagementViewSet.as_view({"patch": "partial_update"})

urlpatterns = [
    path("auth/me/", CurrentUserView.as_view(), name="current-user"),
    path("admin/nannies/", nanny_list, name="admin-nanny-list"),
    path("admin/nannies/<int:pk>/", nanny_detail, name="admin-nanny-detail"),
]
