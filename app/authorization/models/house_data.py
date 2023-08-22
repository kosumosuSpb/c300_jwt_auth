from django.db import models

from app.authorization.models import CompanyProfile, TenantProfile


class HouseGroup(models.Model):
    """Группа домов"""
    name = models.CharField(max_length=100)
    company = models.ForeignKey(
        CompanyProfile,
        on_delete=models.SET_NULL,
        related_name='house_groups',
        null=True
    )


class House(models.Model):
    """Дом"""
    zip_code = models.CharField(max_length=6)
    city = models.CharField(max_length=255)
    street = models.CharField(max_length=255)
    number = models.CharField(max_length=10)
    letter = models.CharField(max_length=5)
    house_group = models.ForeignKey(
        HouseGroup,
        on_delete=models.CASCADE,
        related_name='houses'
    )


class Area(models.Model):
    """Помещение"""
    number = models.CharField(max_length=50)
    house = models.ForeignKey(
        House,
        on_delete=models.CASCADE,
        related_name='areas'
    )
    # tenants
    # owners


class Owner(models.Model):
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
