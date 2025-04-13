from rest_framework import permissions


class IsAuthorOrReadOnlyPermission(permissions.BasePermission):
    """
    Permission as the name suggest:
    allowed only if user is author
    or gives read only property.
    """
    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )
