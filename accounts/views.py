from rest_framework import generics, permissions, serializers
from rest_framework.views import APIView
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, inline_serializer

from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
)

from .permissions import (
    IsAdministrator,
    IsTechnician,
    IsSupportAgent,
    IsCustomer,
)


class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]


class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class RoleDashboardView(APIView):
    permission_classes = [
        IsAdministrator | IsTechnician | IsSupportAgent | IsCustomer
    ]

    @extend_schema(
        responses=inline_serializer(
            name="RoleDashboardResponse",
            fields={
                "message": serializers.CharField(),
                "username": serializers.CharField(),
                "role": serializers.CharField(),
            },
        )
    )
    def get(self, request):
        return Response({
            "message": "Access granted",
            "username": request.user.username,
            "role": request.user.role,
        })


class TechnicianDashboardView(APIView):
    permission_classes = [IsTechnician]

    @extend_schema(
        responses=inline_serializer(
            name="TechnicianDashboardResponse",
            fields={
                "message": serializers.CharField(),
                "user": serializers.CharField(),
            },
        )
    )
    def get(self, request):
        return Response({
            "message": "Welcome to the technician dashboard",
            "user": request.user.username,
        })


class SupportDashboardView(APIView):
    permission_classes = [IsSupportAgent]

    @extend_schema(
        responses=inline_serializer(
            name="SupportDashboardResponse",
            fields={
                "message": serializers.CharField(),
                "user": serializers.CharField(),
            },
        )
    )
    def get(self, request):
        return Response({
            "message": "Welcome to the support dashboard",
            "user": request.user.username,
        })


class AdministratorDashboardView(APIView):
    permission_classes = [IsAdministrator]

    @extend_schema(
        responses=inline_serializer(
            name="AdministratorDashboardResponse",
            fields={
                "message": serializers.CharField(),
                "user": serializers.CharField(),
            },
        )
    )
    def get(self, request):
        return Response({
            "message": "Welcome to the administrator dashboard",
            "user": request.user.username,
        })