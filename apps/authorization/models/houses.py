from django.db import models

from apps.authorization.models.company_profile import CompanyProfile


class HouseGroup(models.Model):
    """Группа домов"""
    name = models.CharField(max_length=100)
    provider = models.ForeignKey(
        CompanyProfile,
        on_delete=models.SET_NULL,
        related_name='house_groups',
        null=True
    )

    def __repr__(self):
        return f'[group:{self.pk}:{self.name}]'

    def __str__(self):
        return f'[group:{self.pk}:{self.name}]'


class House(models.Model):
    """Дом"""
    zip_code = models.CharField(max_length=6, null=True, blank=True)
    city = models.CharField(max_length=255)
    street = models.CharField(max_length=255)
    number = models.CharField(max_length=10)
    letter = models.CharField(max_length=5)
    house_group = models.ForeignKey(
        HouseGroup,
        on_delete=models.SET_NULL,
        null=True,
        related_name='houses'
    )

    def __repr__(self):
        return f'[house:{self.pk}:{self.street}:{self.number}]'

    def __str__(self):
        return f'[house:{self.pk}:{self.street}:{self.number}]'
