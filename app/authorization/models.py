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
    old_numbers = ArrayField(models.CharField(max_length=13, blank=True), blank=True, null=True)  # поле только для PostgreSQL
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


class OrganizationProfile(models.Model):
    user = models.OneToOneField(
        UserData,
        on_delete=models.PROTECT,
        related_name='organization_profile'
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
    # workers
    # tenants

    def __repr__(self):
        return f'[Org:{self.pk}:{self.name}]'

    def __str__(self):
        return f'[Org:{self.pk}:{self.name}]'


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
    department = models.CharField(max_length=75, verbose_name='Отдел')
    company = models.ForeignKey(
        OrganizationProfile,
        on_delete=models.PROTECT,
        related_name='workers',
        verbose_name='Компания, в которой работает сотрудник'
    )

    def __repr__(self):
        return f'[worker:{self.pk}:{self.first_name} {self.last_name[:1]}.]'

    def __str__(self):
        return f'[worker:{self.pk}:{self.first_name} {self.last_name[:1]}.]'


class TenantProfile(HumanBaseProfile):
    """Житель-человек"""
    # TODO: но жителем и владельцем помещения может быть и организация
    # TODO: добавить сохранение платёжных данных

    user = models.OneToOneField(
        UserData,
        on_delete=models.PROTECT,
        related_name='tenant_profile'
    )
    provider = models.ForeignKey(
        OrganizationProfile,
        on_delete=models.PROTECT,
        related_name='tenants',
        verbose_name='Организация, предоставившая доступ'
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
    area = models.CharField(max_length=255, blank=True, null=True)
    rooms = ArrayField(
        models.CharField(max_length=11, blank=True),
        blank=True,
        null=True
    )  # только для PostgreSQL

    # MEMBERSHIP
    coop_member_date_from = models.DateTimeField(
        verbose_name='Дата принятия в члены ТСЖ/ЖСК',
        default=None,
        blank=True,
        null=True
    )

    # COMPATIBILITY with old auth
    news_count_read = models.IntegerField(
        default=0,
        verbose_name='Количество прочитанных новостей'
    )
    delivery_disabled = models.BooleanField(
        default=False,
        verbose_name='Отключено ли получение рассылки'
    )
    disable_paper_bills = models.BooleanField(default=False)
    family = models.ManyToManyField(
        'TenantProfile',
        on_delete=models.SET_NULL,
        related_name='family',
        verbose_name='Семья'
    )  # те, кто живёт в той же квартире?

    @property
    def is_coop_member(self):
        """Является ли житель членом ТСЖ/ЖСК?"""
        return bool(self.coop_member_date_from)

    def __repr__(self):
        return f'[tenant:{self.pk}:{self.first_name} {self.last_name[:1]}.]'

    def __str__(self):
        return f'[tenant:{self.pk}:{self.first_name} {self.last_name[:1]}.]'

    #

    # coefs = EmbeddedDocumentListField(
    #     Coef,
    #     verbose_name='Значения квартирных коэффициентов',
    # )
    # statuses = EmbeddedDocumentField(
    #     Statuses,
    #     default=Statuses(),
    #     verbose_name='Статусы жильца'
    # )
    # finance_legacy = ListField(
    #     ReferenceField('processing.models.billing.account.Account'),
    #     verbose_name="наследование фин. истории; "
    #                  "айди жителя, от которого наследуется"
    # )
    # cabinet_petition = EmbeddedDocumentField(
    #     Files,
    #     null=True
    # )

    # rating = IntField(verbose_name="Рейтинг жителя")
    # assessment = EmbeddedDocumentField(
    #     AssessmentEmbedded,
    #     verbose_name="Рейтинг жителя",
    # )
    #

    # settings = EmbeddedDocumentField(AccountSettingsEmbedded)
    # # поля человеческого существа

    # photo = EmbeddedDocumentField(
    #     Files,
    #     verbose_name="Фотография работника (для карточки в системе)"
    # )
    # short_name = StringField()
    #
    # # поля жителя-человека
    # renting = EmbeddedDocumentField(
    #     RentingContract,
    #     verbose_name='Договор найма'
    # )

    # is_privileged = BooleanField(
    #     required=True,
    #     default=False,
    # )
    # privileges = EmbeddedDocumentListField(
    #     PrivilegeBind,
    #     verbose_name='Список льгот, закрепленных за жителем'
    # )
    # privileges_info = EmbeddedDocumentField(PrivilegesInfo)
    # last_name_upper = StringField()
    # short_name_upper = StringField()
    # nationality = StringField(
    #     choices=NATIONALITY_CHOICES,
    #     default=Nationality.RUSSIAN,
    #     verbose_name='Национальность'
    # )

    # place_birth_fias = StringField(
    #     null=True,
    #     verbose_name="ФИАС места рождения",
    # )
    # place_origin = EmbeddedDocumentField(PlaceOrigin)
    #
    # # поля юр.лица - собственника помещения
    # name = StringField(verbose_name='Наименование', null=True)
    # legal_form = StringField(
    #     null=True,
    #     verbose_name='Правовая форма',
    # )
    # kpp = StringField(
    #     null=True,
    #     verbose_name='КПП',
    # )
    # ogrn = StringField(
    #     null=True,
    #     verbose_name='ОГРН',
    # )
    # director = EmbeddedDocumentField(
    #     EmbeddedPosition,
    #     verbose_name='Информация о директоре'
    # )
    # accountant = EmbeddedDocumentField(
    #     EmbeddedPosition,
    #     verbose_name='Информация о бухгалтере'
    # )
    # is_developer = BooleanField(
    #     null=True,
    #     verbose_name='Является застройщиком в текущем доме'
    # )
    # do_not_accrual = BooleanField(
    #     null=True,
    #     verbose_name='Начисления не проводятся'
    # )
    # entity = ObjectIdField(verbose_name='Ссылка на справочник организаций')
    # entity_contract = ObjectIdField(verbose_name='Ссылка на договор управления')
    # email_notify = BooleanField(verbose_name='Получать уведомления по почте?')
    # email_slip = BooleanField(verbose_name='Получать квитанции по почте?')
    # _binds = EmbeddedDocumentField(
    #     HouseGroupBinds,
    #     verbose_name='Привязки к организации и группе домов (P,HG и D)'
    # )
    # grace_period = EmbeddedDocumentListField(
    #     ResponsibleTenantGracePeriod,
    #     verbose_name='Льготный период у ответственного жильца для пеней.',
    # )
    # telegram_chats = EmbeddedDocumentListField(TelegramChatId)
    # archived_emails = ListField(StringField())
    # # поля-ошибки

    # is_responsible = BooleanField()
    # tasks = DictField()
    # offsets = DynamicField()
    # update_offsets_sectors = DynamicField()
    # update_saldo = DynamicField()
    # update_sectors = DictField()
    # update_offsets_at = DateTimeField()
    # task = DictField()
    # modified_at = DateTimeField()


# class Permission(models.Model):
#     name = models.CharField(max_length=255, unique=True)
#     description = models.CharField(max_length=255)
#     #
#     create = models.BooleanField(default=False)
#     read = models.BooleanField(default=False)
#     update = models.BooleanField(default=False)
#     delete = models.BooleanField(default=False)
