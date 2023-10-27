import logging

from django.db import models

from apps.authorization.models import (
    CompanyProfile,
    WorkerProfile,
    TenantProfile
)


logger = logging.getLogger(__name__)


class CustomPermissionModel(models.Model):
    """Базовая модель прав"""
    class Meta:
        db_table = "authorization_permissions"
        unique_together = ['type', 'name']

    CREATE = 'CREATE'
    READ = 'READ'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'
    ACTIONS = [CREATE, READ, UPDATE, DELETE]

    TYPE_CHOICES = (
        ('create', CREATE),
        ('read', READ),
        ('update', UPDATE),
        ('delete', DELETE)
    )

    type = models.CharField(max_length=6, choices=TYPE_CHOICES)  # noqa A003
    name = models.CharField(max_length=150)
    desc = models.CharField(max_length=255, blank=True, null=True)
    workers = models.ManyToManyField(
        WorkerProfile,
        related_name='permissions'
    )
    tenants = models.ManyToManyField(
        TenantProfile,
        related_name='permissions'
    )
    companies = models.ManyToManyField(
        CompanyProfile,
        related_name='permissions'
    )
    # permissions_groups - M2M link with perm groups

    @property
    def description(self):
        return self.desc

    def __str__(self):
        return f'<Perm | {self.name} | {self.type}>'

    def __repr__(self):
        return f'<Perm | {self.name} | {self.type}>'

    @classmethod
    def create_permissions(cls, name: str, desc_start='Can') -> list:
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

        for action in cls.ACTIONS:
            # logger.debug('Создание права для %s %s', action, name)
            action = action.lower()
            desc = f'{desc_start} {action} {name}'
            # logger.debug('name: %s, action: %s, desc: %s', name, action, desc)
            perm = cls.objects.create(name=name, type=action, desc=desc)
            crud_perms.append(perm)

        logger.debug('Созданы права: %s', crud_perms)
        return crud_perms


class PermissionGroup(models.Model):
    """
    Набор прав, соответствующий роли пользователя.

    Используется для хранения шаблона, в котором собраны различные права,
    нужные для конкретного пользователя, имеющую какую-то типичную роль.

    Однако набор не является определяющим:
    он только хранит права, которые нужно базово присвоить пользователю:
    после чего их можно будет менять

    """

    name = models.CharField(max_length=100)
    desc = models.CharField(max_length=255, blank=True, null=True)
    permissions = models.ManyToManyField(
        CustomPermissionModel,
        related_name='permissions_groups'
    )

    @property
    def description(self):
        return self.desc
