from django.db import models
from django.contrib.postgres.fields import ArrayField

from apps.authorization.models.user_data import UserData
from apps.authorization.models.base_profiles import UserProfile


class CompanyProfile(UserProfile):
    """
    Профиль компании

    Обязательные поля:
        - user - пользователь, которым является
        - name - название организации
    """
    user = models.OneToOneField(
        UserData,
        on_delete=models.PROTECT,
        related_name='company_profile'
    )
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Название организации'
    )

    bank_details = models.JSONField(
        blank=True,
        null=True,
        verbose_name='Список банковских реквизитов'
    )
    address = models.TextField(
        verbose_name='Юридический адрес компании',
        blank=True,
        null=True
    )
    # departments
    # house_groups
    # owner_areas

    def __repr__(self):
        return f'<org:{self.pk}:{self.name}>'

    def __str__(self):
        return f'<org:{self.pk}:{self.name}>'


class Department(models.Model):
    """Отдел в компании"""
    name = models.CharField(max_length=255)
    company = models.ForeignKey(
        CompanyProfile,
        on_delete=models.CASCADE,
        related_name='departments'
    )
    # workers

    def __str__(self):
        return f'<dep:{self.pk}:{self.name}:{self.company}>'

    def __repr__(self):
        return f'<dep:{self.pk}:{self.name}:{self.company}>'
