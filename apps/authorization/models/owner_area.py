from django.db import models

from apps.authorization.models.area import Area
from apps.authorization.models.company_profile import CompanyProfile
from apps.authorization.models.tenant_profile import TenantProfile


class OwnerArea(models.Model):
    """
    Профиль владельца помещения

    По сути представляет собой кастомную промежуточную таблицу M2M
    """
    part = models.FloatField(default=1.0, verbose_name='Доля владения помещением')
    area = models.ForeignKey(
        Area,
        on_delete=models.CASCADE,
        related_name='owners'
    )
    company_owner = models.ForeignKey(
        CompanyProfile,
        on_delete=models.SET_NULL,
        related_name='owner_areas',
        null=True
    )
    tenant_owner = models.ForeignKey(
        TenantProfile,
        on_delete=models.SET_NULL,
        related_name='owner_areas',
        null=True
    )
