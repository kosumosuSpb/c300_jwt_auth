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
    Department,
    TenantProfile,
    WorkerProfile,
    UserProfile
)

from config.settings import SIMPLE_JWT, ORG, TENANT, WORKER


logger = logging.getLogger(__name__)


class UserServiceException(Exception):
    pass


class UserService(BaseService):
    """Управление пользователем и его профилем"""
    def __init__(self, user_id_or_token: str | int | UserData):
        self.user: UserData = self.get_user(user_id_or_token)

    @classmethod
    def get_user(cls, user_id_or_token: str | int) -> UserData | None:
        """Вернёт модель пользователя UserData"""
        is_user_data = isinstance(user_id_or_token, UserData)
        is_num = isinstance(user_id_or_token, int) or (isinstance(user_id_or_token, str) and user_id_or_token.isdecimal())

        if is_user_data:
            user_model = user_id_or_token
        elif is_num:
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
            password: пароль
            profile: словарь с профилем для создания профиля пользователя
            number: номер лицевого счёта
            **extra_fields: дополнительные поля пользователя

        Returns:
            Модель пользователя UserData
        """
        if not number:
            number = cls._get_number()

        logger.debug('UserService | profile: %s', profile)

        user_type = profile.get('type')
        if not user_type:
            msg = ('В  профиле не указан тип пользователя (type): '
                   'не возможно создать пользователя без указания его типа!')
            logger.error(msg)
            raise AttributeError(msg)

        user = UserData.objects.create_user(
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
        if user_type == ORG:
            profile = cls.create_profile_company(user, profile)
        elif user_type == TENANT:
            profile = cls.create_profile_tenant(user, profile)
        elif user_type == WORKER:
            profile = cls.create_profile_worker(user, profile)
        else:
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

    def validate_human_fields(self, profile: dict) -> bool:
        """Проверяет наличие необходимых ключей в словаре профиля"""
        # TODO

    def mark_as_deleted(self):
        """Помечает пользователя удёленным"""
        logger.debug('mark_as_deleted user: %s', self.user)
        self.user.is_deleted = True
        self.user.is_active = False

    def delete_user(self):
        """Удаление текущего пользователя"""
        logger.debug('Запущено удаление пользователя %s', self.user)
        self.user.delete()
        logger.debug('Пользователь %s успешно удалён', self.user)
        return

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
            msg = 'Не верный тип user_id! должен быть str или int'
            logger.error(msg)
            raise TypeError(msg)

        user_id = int(user_id)
        try:
            user_model = UserData.objects.get(pk=user_id)
        except ObjectDoesNotExist as dne:
            msg = f'Пользователь с id {user_id} не найден: {dne}'
            logger.error(msg)
            raise KeyError(msg)

        return user_model

    def send_activation_mail(self):
        """Отправка письма с активацией"""


    def activate_user(self, activation_code: str):
        """Активация пользователя"""
        is_correct_code = self.user.activation_code == activation_code

        if is_correct_code:
            self.user.activation_code = None
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
