from rest_framework import permissions


class CreatorOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return (
            obj.creator == request.user
            or request.method in permissions.SAFE_METHODS
        )
