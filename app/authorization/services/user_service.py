import logging
import random
import datetime

import jwt
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.serializers import TokenVerifySerializer
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.exceptions import ValidationError

from app.authorization.services.base_service import BaseService
from app.authorization.models import (
    UserData,
    CompanyProfile,
    TenantProfile,
    WorkerProfile,
    UserProfile
)
from config.settings import SIMPLE_JWT


logger = logging.getLogger(__name__)


class UserServiceException(Exception):
    pass


class UserService(BaseService):
    """Управление пользователем и его профилем"""
    def __init__(self, user_id_or_token: str | int):
        self.user: UserData = self.get_user(user_id_or_token)

    @classmethod
    def get_user(cls, user_id_or_token: str | int) -> UserData | None:
        """Вернёт модель пользователя UserData"""
        is_num = isinstance(user_id_or_token, int) or (isinstance(user_id_or_token, str) and user_id_or_token.isdecimal())

        if is_num:
            user_model = cls._get_user_from_user_id(user_id_or_token)
        else:
            user_model = cls._get_user_from_token(user_id_or_token)
        return user_model

    def get_permissions(self):
        """Возвращает права пользователя. Демонстрационно: в реальности пока бесполезно"""
        permissions_set = self.user.get_user_permissions()
        permissions = {perm: self.user.has_perm(perm) for perm in permissions_set}

        is_list = [field.name for field in self.user._meta.fields if field.name.startswith('is_')]
        flags = {field: getattr(self.user, field) for field in is_list}
        permissions.update(flags)
        return permissions

    @staticmethod
    def verify_token(token: str) -> bool:
        """Верификация токена"""
        serializer = TokenVerifySerializer(data=token)
        try:
            serializer.is_valid(raise_exception=True)
        except (ValidationError, TokenError) as ve:
            logging.error('Ошибка токена: %s', ve)
            return False
        return True

    @classmethod
    def create_user(
            cls,
            user_type: str,
            email: str,
            password: str | None = None,
            number: str | None = None,
            **extra_fields
    ) -> UserData:
        """Создание пользователя и его профиля"""
        if not number:
            number = cls._get_number()

        if not user_type:
            msg = ('Не указан тип пользователя (user_type): '
                   'не возможно создать пользователя без указания его типа!')
            logger.error(msg)
            raise AttributeError(msg)

        is_admin = extra_fields.get('is_admin', False)
        is_staff = extra_fields.get('is_staff', False)
        is_superuser = extra_fields.get('is_superuser', False)

        user = UserData.objects.create_user(
            email=email,
            password=password,
            number=number,
            # type=[user_type],
            phones={},
            comment='',
            avatar=None,
            inn=None,
            is_admin=is_admin,
            is_active=False,
            is_staff=is_staff,
            is_superuser=is_superuser
        )
        logger.debug('Created user: %s', user)

        profile = cls.create_user_profile(user, user_type, **extra_fields)
        logger.debug('Created profile: %s', profile)

        return user

    @classmethod
    def create_user_profile(
            cls,
            user: UserData,
            user_type: str,
            **extra_fields
    ) -> UserProfile:
        """
        Создание профиля пользователя в зависимости от типа и пользователя с его профилем

        Для профиля-организации нужно ввести: name
        Для профиля-сотрудника: first_name, last_name, sex, birth_date

        Args:
            user: Модель пользователя
            user_type: Тип пользователя: Worker, Tenant, Company
            **extra_fields: дополнительные поля (у разных профилей разные)

        Returns: Профиль пользователя (UserProfile)

        """
        if user_type == UserData.ORG:
            profile = cls.create_profile_company(user, **extra_fields)
        elif user_type == UserData.TENANT:
            profile = cls.create_profile_tenant(user, **extra_fields)
        elif user_type == UserData.WORKER:
            profile = cls.create_profile_worker(user, **extra_fields)
        else:
            msg = 'Указан не верный тип профиля пользователя!'
            logger.error(msg)
            raise UserServiceException(msg)

        return profile

    @staticmethod
    def create_profile_company(
            user: UserData,
            org_name: str,
            **extra_fields
    ) -> CompanyProfile:
        """Создание профиля организации"""
        address = extra_fields.get('org_address')
        bank_details = extra_fields.get('bank_detailes')
        company = CompanyProfile.objects.create(
            user=user,
            name=org_name,
            address=address,
            bank_details=bank_details,
            **extra_fields
        )
        return company

    @staticmethod
    def create_profile_tenant(
            user: UserData,
            first_name: str,
            last_name: str,
            birth_date: datetime.datetime,
            sex: str,
            surname=None,
            **extra_fields
    ) -> TenantProfile:
        """Создание профиля жителя"""
        tenant = TenantProfile.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            surname=surname,
            birth_date=birth_date,
            sex=sex,
            **extra_fields
        )
        return tenant

    @staticmethod
    def create_profile_worker(
            user: UserData,
            first_name: str,
            last_name: str,
            birth_date: datetime.datetime,
            sex: str,
            company: CompanyProfile,
            surname=None,
            **kwargs
    ) -> WorkerProfile:
        """Создание профиля сотрудника"""
        worker = WorkerProfile.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            surname=surname,
            company=company,
            birth_date=birth_date,
            sex=sex,
            **kwargs
        )
        return worker

    def update_email(self):
        """Обновление (изменение) адреса электронной почты"""
        pass

    @staticmethod
    def _get_number() -> str:
        """Временная реализация метода получения уникального номера для пользователя"""
        while True:
            number = random.randint(1000000000000, 9999999999999)
            number = str(number)

            try:
                UserData.objects.get(number=number)
            except ObjectDoesNotExist:
                break
        return number

    def del_user(self):
        """Удаление текущего пользователя"""
        status = self._del_user(self.user.pk)
        return status

    @staticmethod
    def _del_user(user_id: int | None = None):
        """Удаление пользователя"""
        logger.debug('Запущено удаление пользователя %s', user_id)
        assert isinstance(user_id, int), 'Тип данных user_id должен быть int или None!'
        try:
            user: UserData = UserData.objects.get(pk=user_id)
        except ObjectDoesNotExist as e:
            logger.error('Пользователь с id: %s не найден: %s', user_id, e)
            return False
        user.delete()
        logger.debug('Пользователь %s успешно удалён', user)
        return True

    @classmethod
    def get_user_id_from_token(cls, token: str) -> int | None:
        """Вернуть user_id из токена"""
        algorythm = SIMPLE_JWT.get('ALGORITHM')
        secret_key = SIMPLE_JWT.get('SIGNING_KEY')

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
        logger.debug('user_id from token: %s', user_id)
        return user_id

    @classmethod
    def _get_user_from_token(cls, token) -> UserData:
        """Возвращает пользователя, доставая его из токена"""
        user_id = cls.get_user_id_from_token(token)
        user_model = cls._get_user_from_user_id(user_id)
        return user_model

    @staticmethod
    def _get_user_from_user_id(user_id: str | int) -> UserData | None:
        """Вернёт модель пользователя"""
        if not isinstance(user_id, (str, int)):
            logger.error('Не верный тип user_id! должен быть str или int')
            return

        user_id = int(user_id)
        user_model = UserData.objects.get(pk=user_id)
        return user_model
