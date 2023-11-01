import logging

from django.db.models import QuerySet

from apps.authorization.services.base_service import BaseService
from apps.authorization.models.permissions import PermissionModel


logger = logging.getLogger(__name__)


class PermissionService(BaseService):
    """Класс для работы с правами"""

    @staticmethod
    def create_permissions(name: str, description='Can') -> list[PermissionModel]:
        """
        Создаёт CRUD права

        Args:
            name: Имя права
            desc_start: Начало строки описания - по-умолчанию "Can",
                например: "Can read something". Здесь read подставляется автоматически,
                а something - это поле name.

        Returns:
            list, Список созданных прав
        """
        crud_perms = []

        for action in PermissionModel.ACTIONS:
            # logger.debug('Создание права для %s %s', action, name)
            action = action.lower()
            perm_description = f'{description} {action} {name}'
            # logger.debug('name: %s, action: %s, desc: %s', name, action, desc)
            perm = PermissionModel.objects.create(name=name, action=action, description=perm_description)
            crud_perms.append(perm)

        logger.debug('Созданы права: %s', crud_perms)
        return crud_perms

    @staticmethod
    def create_one_permission(name: str, action: str, desc_start='Can') -> PermissionModel:
        """
        Создаёт одно CRUD право

        Args:
            name: Имя права
            action: Действие
            desc_start: Начало строки описания - по-умолчанию "Can",
                например: "Can read something". Здесь read подставляется автоматически,
                а something - это поле name.

        Returns:
            list, Список созданных прав
        """
        assert action.upper() in PermissionModel.ACTIONS, \
            f'Действие должно быть одним из вариантов: {PermissionModel.ACTIONS}!'

        # logger.debug('Создание права для %s %s', action, name)
        action = action.lower()
        desc = f'{desc_start} {action} {name}'
        # logger.debug('name: %s, action: %s, desc: %s', name, action, desc)
        perm = PermissionModel.objects.create(name=name, action=action, desc=desc)

        logger.debug('Создано право: %s', perm)
        return perm

    @staticmethod
    def get_permissions(name: str) -> QuerySet[PermissionModel]:
        """Возвращает CRUD-правда по имени"""
        perms: QuerySet = PermissionModel.objects.filter(name=name)

        if not perms:
            logger.debug('CRUD-правда по имени "%s" не найдены', name)

        return perms

    @staticmethod
    def delete_permissions(name: str):
        """Удаляет CRUD-правда по введённому имени"""
        logger.debug('delete_permissions starts, name: %s', name)
        perms: QuerySet = PermissionModel.objects.filter(name=name)

        if not perms:
            logger.debug('CRUD-правда по имени "%s" не найдены', name)
            return

        perms.delete()
