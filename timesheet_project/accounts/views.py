from rest_framework import mixins, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .permissions import IsAdmin
from .serializers import (
    AccountSetupCompleteSerializer,
    AccountSetupRequestSerializer,
    AccountSetupValidateSerializer,
    ChangePasswordSerializer,
    CurrentUserSerializer,
    DashboardUserSerializer,
    NannySerializer,
)
from .services import send_account_setup_email


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


class AccountSetupRequestView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = AccountSetupRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.save(), status=status.HTTP_200_OK)


class AccountSetupValidateView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        serializer = AccountSetupValidateSerializer(data={"token": request.query_params.get("token", "")})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AccountSetupCompleteView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = AccountSetupCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "detail": "Account setup completed successfully.",
                "user": CurrentUserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class NannyManagementViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = NannySerializer
    permission_classes = [IsAdmin]
    queryset = User.objects.filter(
        role=User.Role.NANNY,
        is_superuser=False,
    ).order_by("first_name", "last_name", "username")

    def perform_create(self, serializer):
        user = serializer.save(role=User.Role.NANNY)
        send_account_setup_email(user)


class DashboardUserManagementViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = DashboardUserSerializer
    permission_classes = [IsAdmin]
    queryset = User.objects.filter(
        role__in=[User.Role.OFFICE, User.Role.ADMIN],
        is_superuser=False,
    ).order_by("role", "first_name", "last_name", "username")

    def perform_create(self, serializer):
        user = serializer.save()
        send_account_setup_email(user)
