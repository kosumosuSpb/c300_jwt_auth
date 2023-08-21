from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.postgres.fields import ArrayField


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
    # user types
    ORG = 'organization'
    WORKER = 'worker'
    TENANT = 'tenant'

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    TYPE_CHOICES = (
        (WORKER, 'Worker'),
        (TENANT, 'Tenant'),
        (ORG, 'Organization'),
    )

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
    is_active = models.BooleanField(default=True)  # аналог has_access из с300
    is_staff = models.BooleanField(default=False)  # возможно, не нужно
    is_superuser = models.BooleanField(default=False)

    # ADDITIONAL FIELDS
    type = models.CharField(
        max_length=25,
        choices=TYPE_CHOICES,
        blank=True,
        null=True
    )
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
    def full_name(self):
        return self.get_full_name()

    def get_full_name(self):
        if self.type in (self.WORKER, self.TENANT):
            return self.profile.first_name + ' ' + self.profile.last_name
        elif self.type == self.ORG:
            return self.profile.name

    @property
    def profile(self):
        """Возвращает профиль пользователя в зависимости от его типа"""
        return (
            self.organization_profile if self.type == self.ORG else
            self.worker_profile if self.type == self.WORKER else
            self.tenant_profile if self.type == self.TENANT else
            None
        )

    def __str__(self):
        return f'[user:{self.pk}:{self.email}]'

    def __repr__(self):
        return f'[user:{self.pk}:{self.email}]'
