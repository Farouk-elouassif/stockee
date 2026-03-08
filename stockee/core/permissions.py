from rest_framework import permissions


class IsAdminRole(permissions.BasePermission):
    """
    Custom permission to only allow users with admin role or Django superusers.
    """
    message = "Admin access required."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Django superusers are always admin
        if request.user.is_superuser:
            return True
        
        # Check custom role in profile
        if hasattr(request.user, 'profile'):
            return request.user.profile.role == 'admin'
        return False


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to access it.
    """
    message = "You don't have permission to access this resource."

    def has_object_permission(self, request, view, obj):
        # Check if the object has a 'user' attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allow read access to anyone, write access only to admins or superusers.
    """
    def has_permission(self, request, view):
        # Allow GET, HEAD, OPTIONS requests
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for admin
        if not request.user.is_authenticated:
            return False
        
        # Django superusers are always admin
        if request.user.is_superuser:
            return True
        
        # Check custom role in profile
        if hasattr(request.user, 'profile'):
            return request.user.profile.role == 'admin'
        return False
