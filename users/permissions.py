# users/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdmin(BasePermission):
    """Only Administrators can access this view."""
    message = "Access restricted to Administrators only."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_admin
        )


class IsOfficer(BasePermission):
    """Only Boarding Officers can access this view."""
    message = "Access restricted to Boarding Officers only."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_officer
        )


class IsAdminOrOfficer(BasePermission):
    """Administrators and Boarding Officers can access this view."""
    message = "Access restricted to Administrators and Boarding Officers."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_admin or request.user.is_officer)
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission:
    - Admins can access any object.
    - Other users can only access their own object.
    """
    message = "You do not have permission to access this resource."

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        return obj == request.user


class IsAdminOrReadOnly(BasePermission):
    """
    Admins have full access.
    All other authenticated users get read-only access.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_admin