from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .permissions import IsAdmin
from .serializers import CurrentUserSerializer, NannySerializer


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(CurrentUserSerializer(request.user).data)


class NannyManagementViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    serializer_class = NannySerializer
    permission_classes = [IsAdmin]
    queryset = User.objects.filter(role=User.Role.NANNY).order_by("first_name", "last_name", "username")

    def perform_create(self, serializer):
        serializer.save(role=User.Role.NANNY)
