from django.db import models

from app.authorization.models.profiles import OrganizationProfile, TenantProfile


class HouseGroup(models.Model):
    """"""
    name = models.CharField(max_length=100)
    # organization =


class House(models.Model):
    """"""
    zip_code = models.CharField(max_length=6)
    city = models.CharField(max_length=255)
    street = models.CharField(max_length=255)
    house_group = models.ForeignKey(
        HouseGroup,
        on_delete=models.CASCADE,
        related_name='houses'
    )


class Area(models.Model):
    """"""
    number = models.CharField(max_length=50)
    house = models.ForeignKey(
        House,
        on_delete=models.CASCADE,
        related_name='areas'
    )
    tenants = models.ManyToManyField(
        TenantProfile,
        related_name='areas'
    )
    # owners


class Owner(models.Model):
    """Профиль владельца помещения"""
    part = models.FloatField(default=1.0, verbose_name='Доля владения помещением')
    area = models.ForeignKey(
        Area,
        on_delete=models.CASCADE,
        related_name='owners'
    )
    organization_owner = models.ForeignKey(
        OrganizationProfile,
        on_delete=models.SET_NULL,
        related_name='owner_areas'
    )
    tenant_owner = models.ForeignKey(
        TenantProfile,
        on_delete=models.SET_NULL,
        related_name='owner_areas'
    )
