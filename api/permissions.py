from rest_framework.permissions import BasePermission

# Только автор может изменять объект, остальные могут только читать
class IsAuthorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in ('GET',) or obj.author == request.user
