from rest_framework.permissions import BasePermission

class IsAdminUserType(BasePermission):
    """
    Custom permission to allow only users with type 'admin'.
    """
    def has_permission(self, request, view):
        return request.user and request.user.type == 'admin'


class IsUserType(BasePermission):
    """
    Custom permission to allow only users with type 'user'.
    """
    def has_permission(self, request, view):
        return request.user and request.user.type == 'user'
