import datetime
import logging
from typing import Iterable

import jwt
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet
from rest_framework_simplejwt.serializers import TokenVerifySerializer
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.exceptions import ValidationError

from apps.authorization.services.base_service import BaseService
from apps.authorization.models import (
    CompanyProfile,
    PermissionModel,
    UserProfile,
    UserData,
    TenantProfile,
    WorkerProfile,
)


logger = logging.getLogger(__name__)


class UserServiceException(Exception):
    pass


class ActivationError(UserServiceException):
    pass


class UserService(BaseService):
    """Управление пользователем и его профилем"""
    def __init__(self, user_id_or_token: str | int | UserData):
        self.user: UserData = self.get_user(user_id_or_token)

    @classmethod
    def get_user(cls, user: str | int) -> UserData | None:
        """Вернёт модель пользователя UserData"""
        is_user_data = isinstance(user, UserData)
        is_email = isinstance(user, str) and '@' in user
        is_num = isinstance(user, int) or (isinstance(user, str) and user.isdecimal())

        if is_user_data:
            user_data = user
        elif is_num:
            user_data = cls._get_user_from_user_id(user)
        elif is_email:
            user_data = cls._get_user_from_email(user)
        else:
            user_data = cls._get_user_from_token(user)
        return user_data

    def get_permissions(self) -> dict:
        """Возвращает права пользователя"""
        permissions = {f'{perm.name} {perm.action}': True for perm in self.user.all_permissions}

        django_permissions_set = self.user.get_user_permissions()
        django_permissions = {perm: self.user.has_perm(perm) for perm in django_permissions_set}

        is_list = [field.name for field in self.user._meta.fields if field.name.startswith('is_')]
        flags = {field: getattr(self.user, field) for field in is_list}

        permissions.update(flags)
        permissions.update(django_permissions)
        return permissions

    @staticmethod
    def verify_token(token: dict | str) -> bool:
        """Верификация токена"""
        logger.debug('verify_token | Пришёл токен на валидацию: %s', token)

        if isinstance(token, str):
            token = {'token': token}

        serializer = TokenVerifySerializer(data=token)
        try:
            serializer.is_valid(raise_exception=True)
        except (ValidationError, TokenError) as ve:
            logging.error('Ошибка валидации токена: %s', ve)
            return False
        return True

    @classmethod
    def create_user(
            cls,
            email: str,
            password: str | None = None,
            *,
            profile: dict,
            number: str | None = None,
            **extra_fields
    ) -> UserData:
        """
        Создание пользователя и его профиля

        Args:
            email: электронная почта
            password (object): пароль
            profile: словарь с профилем для создания профиля пользователя
            number: номер лицевого счёта
            **extra_fields: дополнительные поля пользователя

        Returns:
            Модель пользователя UserData
        """
        logger.debug('UserService | profile: %s', profile)

        user_type = profile.get('type')
        if not user_type:
            msg = ('В  профиле не указан тип пользователя (type): '
                   'не возможно создать пользователя без указания его типа!')
            logger.error(msg)
            raise AttributeError(msg)

        logger.debug('EXTRA FIELDS: %s', extra_fields)

        user: UserData = UserData.objects.create_user(
            email=email,
            password=password,
            number=number,
            **extra_fields
        )
        logger.debug('Created user: %s', user)

        profile = cls.create_user_profile(user, profile)
        logger.debug('Created profile: %s', profile)

        return user

    @classmethod
    def create_user_profile(
            cls,
            user: UserData,
            profile: dict
    ) -> UserProfile:
        """
        Создание профиля пользователя в зависимости от типа и пользователя с его профилем

        Args:
            user: Модель пользователя
            profile: словарь с данными для создания профиля пользователя

        Returns: Профиль пользователя (UserProfile)

        """
        user_type = profile.get('type')

        match user_type:
            case settings.ORG:
                profile = cls.create_profile_company(user, profile)
            case settings.TENANT:
                profile = cls.create_profile_tenant(user, profile)
            case settings.WORKER:
                profile = cls.create_profile_worker(user, profile)
            case _:
                msg = 'Указан не верный тип профиля пользователя!'
                logger.error(msg)
                raise UserServiceException(msg)

        return profile

    @staticmethod
    def create_profile_company(
            user: UserData,
            profile: dict
    ) -> CompanyProfile:
        """Создание профиля организации"""
        assert 'name' in profile, 'Нет необходимого ключа "name" в профиле!'
        company = CompanyProfile.objects.create(user=user, **profile)
        return company

    @staticmethod
    def create_profile_tenant(
            user: UserData,
            profile: dict
    ) -> TenantProfile:
        """Создание профиля жителя"""
        # TODO: добавить проверку наличия необходимых полей в словаре профиля
        #  метод validate_human_fields
        tenant = TenantProfile.objects.create(user=user, **profile)
        return tenant

    @staticmethod
    def create_profile_worker(
            user: UserData,
            profile: dict
    ) -> WorkerProfile:
        """Создание профиля сотрудника"""
        # TODO: добавить проверку наличия необходимых полей в словаре профиля
        #  метод validate_human_fields
        worker = WorkerProfile.objects.create(user=user, **profile)
        return worker

    def update_email(self):
        """Обновление (изменение) адреса электронной почты"""
        # TODO
        pass

    def update_password(self):
        """Обновление (изменение) пароля"""
        # TODO
        pass

    def update_user(self, new_user_data: dict):
        """
        Полное обновление информации о пользователе и его профиля.

        Не обновляет тип юзера, мыло, пароль, активационные коды

        Предполагается, что данные сюда приходят уже после сериализации и валидации

        Args:
            new_user_data: словарь с новыми данными по юзеру

        Returns:
            None
        """
        logger.debug('UserService | update_user | new_user_data: %s', new_user_data)

        new_profile: dict = new_user_data.pop('profile')
        profile_id = self.user.profile.pk

        user_qs: QuerySet = UserData.objects.filter(pk=self.user.pk)
        user_updated_rows = user_qs.update(**new_user_data)
        logger.debug('UserService | update_user | user_updated_rows count: %s',
                     user_updated_rows)

        profile_model: UserProfile = self.get_profile_model(self.user.type)
        profile_qs: QuerySet = profile_model.objects.filter(pk=profile_id)
        profile_updated_rows = profile_qs.update(**new_profile)
        logger.debug('UserService | update_user | profile_updated_rows count: %s',
                     profile_updated_rows)

    def validate_human_fields(self, profile: dict) -> bool:
        """Проверяет наличие необходимых ключей в словаре профиля"""
        # TODO

    def mark_as_deleted(self):
        """Помечает пользователя удёленным"""
        logger.debug('mark_as_deleted user: %s', self.user)
        self.user.is_deleted = True
        self.user.is_active = False
        self.user.save()

    def delete_user(self, user: UserData | None = None):
        """Удаление текущего пользователя"""
        user = user or self.user
        self._delete_user(user)

    @staticmethod
    def _delete_user(user: UserData):
        logger.debug('Запущено удаление пользователя %s', user)

        user.profile.delete()
        user.delete()

        logger.debug('Пользователь %s успешно удалён', user)

    @classmethod
    def _purge_users(cls):
        """
        Удаляет всех пользователей и все профили из БД.
        Использовать только на тестовой базе
        с не большим количеством пользователей!

        """
        logger.warning('ВНИМАНИЕ, ЗАПУЩЕНО УДАЛЕНИЕ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ И ПРОФИЛЕЙ!')
        users: QuerySet[UserData] = UserData.objects.all()

        if not users:
            logger.debug('Пользователи в БД не найдены')
            return

        for user in users:
            cls._delete_user(user)

        logger.warning('ВСЕ ПОЛЬЗОВАТЕЛИ И ПРОФИЛИ УДАЛЕНЫ ИЗ БД')

    @classmethod
    def get_user_id_from_token(cls, token: str) -> int | None:
        """Вернуть user_id из токена"""
        algorythm = settings.SIMPLE_JWT.get('ALGORITHM')
        secret_key = settings.SIMPLE_JWT.get('SIGNING_KEY')

        logger.info('Token type: %s, Token: %s', type(token), token)

        try:
            # на этом моменте по сути тоже происходит верификация
            # и если токен истёк по времени, то будет исключение
            payload = jwt.decode(token, secret_key, algorithms=[algorythm, ])
        except jwt.exceptions.ExpiredSignatureError as e:
            logger.error('Ошибка JWT: %s', e)
            return

        logger.debug('PAYLOAD: %s', payload)
        user_id = payload.get('user_id')
        date_exp = payload.get('exp')
        date_exp = datetime.datetime.fromtimestamp(date_exp) if date_exp else None
        logger.debug('date expiration: %s', date_exp)
        logger.debug('user_id from token: %s', user_id)
        return user_id

    @classmethod
    def _get_user_from_token(cls, token) -> UserData | None:
        """Возвращает пользователя, доставая его из токена"""
        user_id = cls.get_user_id_from_token(token)

        if not user_id:
            msg = 'Срок действия токена истёк!'
            logger.error(msg)
            raise ValidationError(msg)

        user_model = cls._get_user_from_user_id(user_id)
        return user_model

    @staticmethod
    def _get_user_from_user_id(user_id: str | int) -> UserData:
        """Вернёт модель пользователя"""
        if not isinstance(user_id, (str, int)):
            msg = 'Не верный тип user_id! должен быть str или int'
            logger.error(msg)
            raise TypeError(msg)

        user_id = int(user_id)
        try:
            user_data = UserData.objects.get(pk=user_id)
        except ObjectDoesNotExist as dne:
            msg = f'Пользователь с id {user_id} не найден: {dne}'
            logger.error(msg)
            raise ObjectDoesNotExist(msg)

        return user_data

    @staticmethod
    def _get_user_from_email(email: str) -> UserData | None:
        """Вернёт пользователя по email"""
        if not isinstance(email, str,):
            msg = 'Не верный тип email! должен быть str'
            logger.error(msg)
            raise TypeError(msg)

        try:
            user_data = UserData.objects.get(email=email)
        except ObjectDoesNotExist as dne:
            msg = f'Пользователь с id {email} не найден: {dne}'
            logger.error(msg)
            raise ObjectDoesNotExist(msg)

        return user_data

    def activate_user(self, activation_code: str):
        """Активация пользователя"""
        logger.debug('Запущена активация пользователя %s', self.user)

        if not self.user.activation_code:
            msg = 'Нет кода активации у пользователя, возможно, он уже активирован'
            logger.error(msg)
            raise ActivationError(msg)

        is_correct_code = self.user.activation_code == activation_code

        if is_correct_code:
            self.user.activation_code = None

            if self.user.is_active:
                logger.warning('Пользователь %s уже был активен', self.user)

            self.user.is_active = True
            self.user.get_access_date = datetime.datetime.now()
            self.user.save()
        else:
            msg = 'Не верный код активации'
            logger.error(msg)
            raise ValueError(msg)

    def manual_activate_user(self):
        """Ручная активация пользователя"""
        logger.debug('Запущена ручная активация пользователя %s', self.user)
        self.user.activation_code = None
        self.user.is_active = True
        self.user.get_access_date = datetime.datetime.now()
        self.user.save()

    # PERMISSIONS

    @staticmethod
    def find_permissions(perms: Iterable[PermissionModel | str]) -> QuerySet:
        """Возвращает QuerySet с правами"""

        if not isinstance(perms, (list, set, tuple, QuerySet)):
            logger.debug('find_permissions: создаём кортеж..')
            perms = (perms, )

        if isinstance(perms, set):
            perms = tuple(perms)

        if isinstance(perms[0], str):
            permissions_models: QuerySet = PermissionModel.objects.filter(name__in=perms)
        elif isinstance(perms[0], PermissionModel):
            permissions_models = perms
        else:
            msg = (f'find_permissions: передан не верный тип элементов в списке прав: '
                   f'допустим str или PermissionModel, а передан: {type(perms[0])}')
            logger.error(msg)
            raise TypeError(msg)

        if not permissions_models:
            msg = f'add_permissions: не найдено прав с такими именами: {perms}'
            logger.error(msg)
            raise ObjectDoesNotExist(msg)

        return permissions_models

    def add_permissions(self, perms: Iterable[PermissionModel | str]) -> QuerySet:
        """
        Добавление списка прав профилю пользователя

        Args:
            perms: права PermissionModel (список, кортеж, множество или QuerySet)
        """
        logger.debug('Добавление пользователю %s прав %s', self.user, perms)
        permissions_models = self.find_permissions(perms)

        if self.user.type == settings.ORG:
            new_perms = permissions_models
        else:
            parent_perms = self.get_parent_perms()
            new_perms = parent_perms.intersection(permissions_models)
            if new_perms != perms:
                logger.warning('Пользователю %s добавлены только те права, '
                               'которые есть у компании: %s',
                               self.user, new_perms)

        self.user.profile.permissions.add(*new_perms)

        return new_perms

    def add_one_permission(self, perm: PermissionModel | str):
        """
        Добавление одного права профилю пользователя (только read, только create итд..)

        Args:
            perm: право PermissionModel (список, кортеж, множество или QuerySet)
        """
        logger.debug('Добавление пользователю %s права %s', self.user, perm)

        if isinstance(perm, str):
            permission_model: PermissionModel = PermissionModel.objects.get(name=perm)
        elif isinstance(perm, PermissionModel):
            permission_model = perm
        else:
            msg = (f'Передан не верный тип данных! '
                   f'Ожидается str или PermissionModel, а пришёл: {type(perm)}')
            logger.error(msg)
            raise TypeError(msg)

        if self.user.type == settings.ORG:
            self.user.profile.permissions.add(permission_model)
        else:
            parent_perm = self.get_parent_perms()

            if perm not in parent_perm:
                msg = ('У компании пользователя нет такого права, '
                       'поэтому невозможно его выдать пользователю')
                logger.warning(msg)
                return

            self.user.profile.permissions.add(permission_model)

    def add_permission(self, perm: PermissionModel):
        """Добавление одного права пользователю"""
        assert isinstance(perm, PermissionModel), 'perm должен быть объектом PermissionModel!'
        self.add_permissions((perm, ))

    def delete_permissions(self, perms: Iterable[PermissionModel | str]):
        """Удаление CRUD-прав по введённым именам прав, либо самим правам (PermissionModel)"""
        logger.debug('Удаление прав %s пользователя %s', perms, self.user)

        permissions_models = self.find_permissions(perms)
        self.user.profile.permissions.remove(*permissions_models)

    def get_parent_perms(self):
        """Получает разрешения родительских профилей"""
        if self.user.type == settings.ORG:
            return

        permissions = self._get_parent_perms(self.user.pk, self.user.type)

        return permissions

    @staticmethod
    def _get_parent_perms(user_id: int | str, user_type: str) -> QuerySet:
        """Получает разрешения родительского профиля, в зависимости от типа профиля"""
        assert isinstance(user_id, (str, int)), 'user_id должен быть str или int!'
        assert user_type in (settings.WORKER, settings.TENANT, settings.ORG), 'Не верный user_type!'

        profile_name = user_type + '_profile'

        user = UserData.objects.select_related(f'{profile_name}__department__company').get(pk=user_id)
        parent_perms = user.profile.department.company.permissions.all()

        return parent_perms
