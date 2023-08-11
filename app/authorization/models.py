from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


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
    REQUIRED_FIELDS = []

    TYPE_CHOICES = (
        ('worker', 'Worker'),
        ('tenant', 'Tenant'),
        ('organization', 'Organization'),
    )

    # BASE FIELDS
    username = None  # поле удалено
    # password = models.CharField(_("password"), max_length=128)  # наследовано
    # name = models.CharField(max_length=100, unique=False)
    email = models.EmailField(max_length=100, unique=True)
    first_name = None
    last_name = None
    date_joined = models.DateTimeField(auto_now_add=True)
    phones = models.JSONField(blank=True, null=True)
    # profile

    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)  # has_access
    is_staff = models.BooleanField(default=False)  # возможно, не нужно
    is_superuser = models.BooleanField(default=False)

    # ADDITIONAL FIELDS
    type = models.CharField(max_length=25, choices=TYPE_CHOICES, blank=True, null=True)
    number = models.CharField(max_length=13, null=True, blank=True)
    comment = models.CharField(max_length=255, null=True, blank=True)
    avatar = models.ImageField(null=True, blank=True)

    # COMPATIBILITY FIELDS
    # get_access_date = models.DateTimeField(auto_now_add=False, null=True, blank=True)

    @property
    def full_name(self):
        return self.get_full_name()

    def get_full_name(self):
        if self.type in ('worker', 'tenant'):
            return self.profile.first_name + ' ' + self.profile.second_name

    def __str__(self):
        return f'[{self.pk}:{self.email}]'

    def __repr__(self):
        return f'[{self.pk}:{self.email}]'


class OrganizationProfile(models.Model):
    user = models.OneToOneField(
        UserData,
        on_delete=models.PROTECT,
        related_name='profile'
    )
    name = models.CharField(max_length=100)
    inn = models.CharField(max_length=12)  # ИНН
    bank_details = models.JSONField(blank=True, null=True)
    address = models.TextField()
    # workers
    # tenants


class WorkerProfile(models.Model):
    user = models.OneToOneField(
        UserData,
        on_delete=models.PROTECT,
        related_name='profile'
    )
    position = models.CharField(max_length=50)  # должность
    department = models.CharField(max_length=50)  # отдел
    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    company = models.ForeignKey(
        OrganizationProfile,
        on_delete=models.PROTECT,
        related_name='workers'
    )


class TenantProfile(models.Model):
    user = models.OneToOneField(
        UserData,
        on_delete=models.PROTECT,
        related_name='profile'
    )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    provider = models.ForeignKey(
        OrganizationProfile,
        on_delete=models.PROTECT,
        related_name='tenants'
    )

    # DOCUMENTS
    snils = models.CharField(blank=True, null=True, required=False)
    # AREA
    area = models.CharField(max_length=255, required=False, blank=True, null=True)
    # MEMBERSHIP

