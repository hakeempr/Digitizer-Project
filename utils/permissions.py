"""
Project-wide DRF permission classes.
"""

from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Allow access only to users with the ADMIN role."""

    message = "Access restricted to administrators."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_admin
        )


class IsApprovedCustomer(BasePermission):
    """Allow access only to approved CUSTOMER accounts."""

    message = "Access restricted to approved customer accounts."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_customer
            and request.user.is_approved
        )


class IsOwnerOrAdmin(BasePermission):
    """Object-level: owner of the object, or an admin, may access."""

    message = "You do not have permission to access this resource."

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        # Support objects that reference the user via `.user` or `.customer`
        owner = getattr(obj, "user", None) or getattr(obj, "customer", None)
        return owner == request.user
