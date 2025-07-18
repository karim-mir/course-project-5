from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrReadOnlyForPublic(BasePermission):
    """
    Пользователь видит только свои привычки и может управлять ими (CRUD).
    Публичные привычки видны всем, но редактировать/удалять их нельзя.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            # SAFE_METHODS = GET, HEAD, OPTIONS
            return obj.is_public or obj.user == request.user

        # Для записи (POST, PUT, PATCH, DELETE) — только владелец
        return obj.user == request.user
