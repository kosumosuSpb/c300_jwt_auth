from django.db import models
from django.contrib.postgres.fields import ArrayField

from app.authorization.models import UserData


class CompanyProfile(models.Model):
    """Профиль компании"""
    user = models.OneToOneField(
        UserData,
        on_delete=models.PROTECT,
        related_name='company_profile'
    )
    name = models.CharField(max_length=100, verbose_name='Название организации')

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
        return f'[Org:{self.pk}:{self.name}]'

    def __str__(self):
        return f'[Org:{self.pk}:{self.name}]'


class Department(models.Model):
    """Отдел в компании"""
    name = models.CharField(max_length=255)
    company = models.ForeignKey(
        CompanyProfile,
        on_delete=models.CASCADE,
        related_name='departments'
    )
    # workers


class HumanBaseProfile(models.Model):
    class Meta:
        abstract = True

    GENDER_TYPE_CHOICES = (
        ('male', 'Мужской'),
        ('female', 'Женский'),
    )

    first_name = models.CharField(max_length=50, verbose_name='Имя')
    last_name = models.CharField(max_length=50, verbose_name='Фамилия')
    surname = models.CharField(max_length=50, verbose_name='Отчество', blank=True, null=True)
    birth_date = models.DateTimeField(verbose_name="Дата рождения")
    sex = models.CharField(max_length=10, choices=GENDER_TYPE_CHOICES, verbose_name="Пол")
    #
    citizenship = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Гражданство"
    )
    military = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Воинская обязанность'
    )
    place_birth = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Место рождения",
    )

    @property
    def full_name(self):
        """Возвращает ФИО"""
        return f'{self.last_name} {self.first_name} {self.surname}'

    @property
    def short_name(self):
        """Возвращает фамилию и инициалы"""
        return f'{self.last_name} {self.first_name[:1]}. {self.surname[:1]}.'

    def __repr__(self):
        return f'[hum:{self.pk}:{self.first_name} {self.last_name[:1]}.]'


class WorkerProfile(HumanBaseProfile):
    user = models.OneToOneField(
        UserData,
        on_delete=models.PROTECT,
        related_name='worker_profile'
    )
    position = models.CharField(max_length=75, verbose_name='Должность')
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='workers',
        verbose_name='Отдел в компании, в которой работает сотрудник'
    )

    @property
    def company(self):
        return self.department.company.pk

    def __repr__(self):
        return f'[worker:{self.pk}:{self.first_name} {self.last_name[:1]}.]'

    def __str__(self):
        return f'[worker:{self.pk}:{self.first_name} {self.last_name[:1]}.]'


class TenantProfile(HumanBaseProfile):
    """Житель-человек"""

    user = models.OneToOneField(
        UserData,
        on_delete=models.PROTECT,
        related_name='tenant_profile'
    )

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

    # AREA
    # areas M2M to Area - в каких помещениях житель живёт
    rooms = ArrayField(
        models.CharField(max_length=11, blank=True),
        blank=True,
        null=True
    )
    # owners_areas

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
