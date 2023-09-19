import logging
from typing import TYPE_CHECKING

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.postgres.fields import ArrayField

from config.settings import ORG, WORKER, TENANT
if TYPE_CHECKING:
    from app.authorization.models import CompanyProfile, HumanBaseProfile


logger = logging.getLogger(__name__)


class UserManager(BaseUserManager):
    use_in_migration = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is Required')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff = True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser = True')

        return self.create_user(email, password, **extra_fields)


class UserData(AbstractUser):
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['password']

    # BASE FIELDS
    username = None  # поле удалено
    # password = models.CharField(_("password"), max_length=128)  # наследовано
    email = models.EmailField(
        max_length=100,
        unique=True,
        verbose_name='Пользовательская электронная почта'
    )
    first_name = None
    last_name = None
    date_joined = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата регистрации'
    )  # аналог created_at
    phones = models.JSONField(
        blank=True,
        null=True,
        verbose_name='Список телефонных номеров'
    )

    is_admin = models.BooleanField(default=False)

    # эти поля наследованы
    # is_active = models.BooleanField(default=True)
    # is_staff = models.BooleanField(default=False)  # возможно, не нужно
    # is_superuser = models.BooleanField(default=False)

    activation_code = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Код активации'
    )

    # RELATIONS
    # company_profile
    # worker_profile
    # tenant_profile

    # ADDITIONAL FIELDS
    number = models.CharField(
        max_length=13,
        null=True,
        blank=True,
        verbose_name='Номер лицевого счёта'
    )
    comment = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Комментарий к пользователю'
    )
    avatar = models.ImageField(null=True, blank=True)
    inn = models.CharField(max_length=12, null=True, blank=True, verbose_name='ИНН')  # ИНН, от 10 до 12 цифр

    # COMPATIBILITY FIELDS
    get_access_date = models.DateTimeField(null=True, blank=True)
    old_numbers = ArrayField(
        models.CharField(max_length=13, blank=True),
        blank=True,
        null=True
    )  # поле только для PostgreSQL
    is_deleted = models.BooleanField(default=False)
    additional_email = models.EmailField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        verbose_name='Дополнительная пользовательская электронная почта'
    )

    @property
    def type(self) -> str:
        """Возвращает тип пользователя"""
        return self.profile.type

    @property
    def full_name(self):
        return self.get_full_name()

    @property
    def all_permissions(self):
        return list(self.permissions.all())

    def get_full_name(self) -> str:
        if self.type == ORG:
            name = self.company_profile.name
        else:
            name = self.profile.first_name + ' ' + self.profile.last_name

        return name

    @property
    def profile(self) -> 'CompanyProfile' or 'HumanBaseProfile':
        """Возвращает профиль пользователя (объект класса UserProfile)"""
        if hasattr(self, 'company_profile'):
            profile = self.company_profile
        elif hasattr(self, 'worker_profile'):
            profile = self.worker_profile
        elif hasattr(self, 'tenant_profile'):
            profile = self.tenant_profile
        else:
            msg = 'Не привязан ни один профиль!'
            logger.error(msg)
            raise TypeError(msg)
        return profile

    def __str__(self):
        return f'[user:{self.pk}:{self.email}]'

    def __repr__(self):
        return f'[user:{self.pk}:{self.email}]'
