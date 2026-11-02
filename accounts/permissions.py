
from rest_framework.permissions import BasePermission


class IsAdministrator(BasePermission):
    """
    Allows access to Django administrators.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )


class IsTechnician(BasePermission):
    """
    Allows access to technicians.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "technician"
        )


class IsSupportAgent(BasePermission):
    """
    Allows access to support agents.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "support"
        )


class IsCustomer(BasePermission):
    """
    Allows access to customers.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "customer"
        )


class IsTechnicianOrAdministrator(BasePermission):

    def has_permission(self, request, view):
        user = request.user

        return (
            user
            and user.is_authenticated
            and (
                user.role == "technician"
                or user.is_superuser
            )
        )


