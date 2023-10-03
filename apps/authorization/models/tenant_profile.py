from django.db import models
from django.contrib.postgres.fields import ArrayField

from apps.authorization.models.user_data import UserData
from apps.authorization.models.base_profiles import HumanBaseProfile
from apps.authorization.models.area import Area


class TenantProfile(HumanBaseProfile):
    """
    Профиль пользователя-жителя

    Обязательные поля:
        - user
    """
    user = models.OneToOneField(
        UserData,
        on_delete=models.PROTECT,
        related_name='tenant_profile'
    )
    # AREA
    area = models.ForeignKey(
        Area,
        on_delete=models.SET_NULL,
        null=True,
        related_name='tenants'
    )  # в каких помещениях житель живёт
    rooms = ArrayField(
        models.CharField(max_length=11, blank=True),
        blank=True,
        null=True
    )
    # owners_areas

    # DOCUMENTS
    snils = models.CharField(max_length=14, blank=True, null=True)  # 14 знаков вместе с пробелом и двумя тире

    #
    gis_uid = models.CharField(
        max_length=10,
        verbose_name='Единый лицевой счет',
        blank=True,
        null=True,
    )
    hcs_uid = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name='Идентификатор ЖКУ'
    )

    @property
    def provider(self):
        """Возвращает компанию-поставщика услуг"""
        company = self.area.house.house_group.provider
        return company

    # MEMBERSHIP - возможно вообще не нужно?
    # coop_member_date_from = models.DateTimeField(
    #     verbose_name='Дата принятия в члены ТСЖ/ЖСК',
    #     default=None,
    #     blank=True,
    #     null=True
    # )

    # COMPATIBILITY with old auth
    # delivery_disabled = models.BooleanField(
    #     default=False,
    #     verbose_name='Отключено ли получение рассылки'
    # )
    # disable_paper_bills = models.BooleanField(default=False)

    # те, кто живёт в той же квартире?
    # это лучше делать через запрос жильцов из квартиры
    # family = models.ManyToManyField(
    #     'TenantProfile',
    #     related_name='family',
    #     verbose_name='Семья'
    # )

    # @property
    # def is_coop_member(self):
    #     """Является ли житель членом ТСЖ/ЖСК?"""
    #     return bool(self.coop_member_date_from)

    def __repr__(self):
        return f'[tenant:{self.pk}:{self.first_name} {self.last_name[:1]}.]'

    def __str__(self):
        return f'[tenant:{self.pk}:{self.first_name} {self.last_name[:1]}.]'
