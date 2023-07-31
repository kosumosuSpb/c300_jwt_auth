import os
import logging

import django
import jwt
from rest_framework_simplejwt.serializers import TokenVerifySerializer
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.exceptions import ValidationError

from app.authorization.models import UserData
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
# django.setup()
from config.settings import SIMPLE_JWT


logger = logging.getLogger(__name__)


class UserService:
    """Управление пользователем"""
    def __init__(self, user: str | int):
        self.user: UserData = self.get_user(user)

    @classmethod
    def get_user(cls, user_id_or_token: str | int) -> UserData | None:
        """Вернёт модель пользователя"""
        is_num = isinstance(user_id_or_token, int) or (isinstance(user_id_or_token, str) and user_id_or_token.isdecimal())

        if is_num:
            user_model = cls._get_user_from_user_id(user_id_or_token)
        else:
            user_model = cls._get_user_from_token(user_id_or_token)
        return user_model

    def get_permissions(self):
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
