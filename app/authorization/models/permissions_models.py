import logging

from django.db import models


logger = logging.getLogger(__name__)


class BaseCustomPermissionModel(models.Model):
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
        ('c', CREATE),
        ('r', READ),
        ('u', UPDATE),
        ('d', DELETE)
    )

    type = models.CharField(max_length=1, choices=TYPE_CHOICES)
    name = models.CharField(max_length=150)
    desc = models.CharField(max_length=255, blank=True, null=True)
    # permissions_groups - M2M link to perm groups

    @property
    def description(self):
        return self.desc

    def __str__(self):
        return f'<Perm | {self.type} | {self.name}>'

    def __repr__(self):
        return f'<Perm | {self.type} | {self.name}>'

    @classmethod
    def create_permissions(cls, name: str, desc: str | None = None):
        """Создаёт CRUD права доступа"""

        for action in cls.ACTIONS:
            logger.debug('Создание права для %s %s', action, name)
            desc = desc or f'Can {action.lower()} {name}'
            perm = cls.objects.create(name=name, type=action, desc=desc)
            logger.debug('Создано право: %s', perm)


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
        BaseCustomPermissionModel,
        related_name='permissions_groups'
    )

    @property
    def description(self):
        return self.desc
