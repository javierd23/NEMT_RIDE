from rest_framework.permissions import BasePermission 
from rest_framework.permissions import PermissionsDenied
from user_auth.models import UserRoles
from user_auth.models import User

from django.shortcuts import get_object_or_404


class IsAdmin(BasePermission):
    """Handling permission for admin users, only admin users can access the endpoint"""

    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):

        if not request.user.is_authenticated:
            raise PermissionsDenied(detail="Authentication credentials were not provided.")
        
        user = request.user
        if user.role and user.role.role == 'Admin':
            return True
        
        raise PermissionsDenied(self.message)