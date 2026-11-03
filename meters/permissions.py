
from rest_framework.permissions import BasePermission


class IsMeterAdministrator(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_superuser
        )


class IsMeterStaff(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        return (
            user.is_authenticated
            and (
                user.is_superuser
                or user.role in ["technician", "support"]
            )
        )

class IsReadingSubmitter(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        return (
            user.is_authenticated
            and (
                user.is_superuser
                or user.role == "technician"
            )
        )

    
