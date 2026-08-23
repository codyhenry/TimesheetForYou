from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .permissions import IsAdmin
from .serializers import (
    ChangePasswordSerializer,
    CurrentUserSerializer,
    DashboardUserSerializer,
    NannySerializer,
)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(CurrentUserSerializer(request.user).data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "detail": "Password changed successfully.",
                "user": CurrentUserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class NannyManagementViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    serializer_class = NannySerializer
    permission_classes = [IsAdmin]
    queryset = User.objects.filter(role=User.Role.NANNY).order_by("first_name", "last_name", "username")

    def perform_create(self, serializer):
        serializer.save(role=User.Role.NANNY)


class DashboardUserManagementViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = DashboardUserSerializer
    permission_classes = [IsAdmin]
    queryset = User.objects.filter(role__in=[User.Role.OFFICE, User.Role.ADMIN]).order_by(
        "role", "first_name", "last_name", "username"
    )
