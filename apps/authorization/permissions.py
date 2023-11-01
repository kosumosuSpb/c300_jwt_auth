import logging

from rest_framework.request import Request
from rest_framework.permissions import BasePermission


logger = logging.getLogger(__name__)


class IsSuperuser(BasePermission):
    """Доступ только для суперпользователей"""

    def has_permission(self, request: Request, view):
        logger.debug('IsSuperuser | has_permission | request.user: %s',
                     request.user)
        logger.debug('IsSuperuser | has_permission | request.user.is_superuser: %s',
                     request.user.is_superuser)
        return bool(request.user and request.user.is_superuser)
