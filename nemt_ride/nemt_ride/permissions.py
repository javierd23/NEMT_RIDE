from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied


class IsAdmin(BasePermission):
    """Handling permission for admin users, only admin users can access the endpoint"""

    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):

        if not request.user.is_authenticated:
            raise PermissionDenied(detail="Authentication credentials were not provided.")
        
        user = request.user
        if user.role and user.role.role == 'admin':
            return True
        
        raise PermissionDenied(self.message)