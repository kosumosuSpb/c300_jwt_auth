import logging

from django.db import models

from apps.authorization.models import (
    CompanyProfile,
    WorkerProfile,
    TenantProfile
)


logger = logging.getLogger(__name__)


class PermissionModel(models.Model):
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
    description = models.CharField(max_length=255, blank=True, null=True)
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
    def desc(self):
        return self.description

    @desc.setter
    def desc(self, value: str):
        self.description = value

    def __str__(self):
        return f'<Perm | {self.name} | {self.type}>'

    def __repr__(self):
        return f'<Perm | {self.name} | {self.type}>'


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
        PermissionModel,
        related_name='permissions_groups'
    )

    @property
    def description(self):
        return self.desc
