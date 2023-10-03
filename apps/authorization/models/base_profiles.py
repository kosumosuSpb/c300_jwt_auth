from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    """Абстрактная модель профиля пользователя"""
    TYPE_CHOICES = (
        (settings.WORKER, 'Worker'),
        (settings.TENANT, 'Tenant'),
        (settings.ORG, 'Company'),
    )

    class Meta:
        abstract = True

    type = models.CharField(max_length=7, choices=TYPE_CHOICES)  # noqa A003


class HumanBaseProfile(UserProfile):
    """
    Базовая модель профиля пользователя-человека

    Обязательные пола:
        - first_name - Имя
        - last_name - Фамилия
        - birth_date - Дата рождения, объект datetime с timezone
        - sex - Пол
    """
    class Meta:
        abstract = True

    REQUIRED_FIELDS = ['first_name', 'last_name', 'birth_date', 'sex']

    GENDER_TYPE_CHOICES = (
        ('male', 'Мужской'),
        ('female', 'Женский'),
    )

    first_name = models.CharField(max_length=50, verbose_name='Имя')
    last_name = models.CharField(max_length=50, verbose_name='Фамилия')
    surname = models.CharField(max_length=50, verbose_name='Отчество', null=True, default='')
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
        return (
            f'{self.last_name} {self.first_name[:1]}. {self.surname[:1]}.' if self.surname else
            f'{self.last_name} {self.first_name[:1]}.'
        )

    def __repr__(self):
        return f'[hum:{self.pk}:{self.first_name} {self.last_name[:1]}.]'

    def __str__(self):
        return f'[hum:{self.pk}:{self.first_name} {self.last_name[:1]}.]'
