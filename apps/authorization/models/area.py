from django.db import models
from django.contrib.postgres.fields import ArrayField

from apps.authorization.models.houses import House


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
