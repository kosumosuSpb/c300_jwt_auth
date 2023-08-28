from rest_framework.request import Request
from rest_framework.permissions import BasePermission


class IsSuperuser(BasePermission):
    """Доступ только для суперпользователей"""

    def has_permission(self, request: Request, view):
        return bool(request.user and request.user.is_superuser)
