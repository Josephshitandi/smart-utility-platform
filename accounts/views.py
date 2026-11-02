
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

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

    def get(self, request):
        return Response({
            "message": "Access granted",
            "username": request.user.username,
            "role": request.user.role,
        })


class TechnicianDashboardView(APIView):
    permission_classes = [IsTechnician]

    def get(self, request):
        return Response({
            "message": "Welcome to the technician dashboard",
            "user": request.user.username,
        })


class SupportDashboardView(APIView):
    permission_classes = [IsSupportAgent]

    def get(self, request):
        return Response({
            "message": "Welcome to the support dashboard",
            "user": request.user.username,
        })


class AdministratorDashboardView(APIView):
    permission_classes = [IsAdministrator]

    def get(self, request):
        return Response({
            "message": "Welcome to the administrator dashboard",
            "user": request.user.username,
        })
