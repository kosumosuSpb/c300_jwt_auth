import logging
import os

import django
import faust
from asgiref.sync import sync_to_async
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.authorization.services.user_service import UserService  # noqa F402


logger = logging.getLogger(__name__)


AUTH_REQUEST = 'auth_request'
AUTH_RESPONSE = 'auth_response'


app = faust.App(
    'auth_bus',
    broker=settings.KAFKA_URL,
    store='rocksdb://',
    autodiscovery=True,
)


class AuthRequest(faust.Record):
    id: str  # noqa A003
    token: str


class AuthResponse(faust.Record):
    id: str  # noqa A003
    status: str
    user_id: str
    permissions: dict


request_topic = app.topic(
    AUTH_REQUEST,
    key_type=bytes,
    value_type=AuthRequest,
)
response_topic = app.topic(
    AUTH_RESPONSE,
    key_type=bytes,
    value_type=AuthResponse,
)


@app.agent(request_topic)
async def auth_requests_agent(stream: faust.streams.Stream[AuthRequest]):
    """Принимает стрим из фауст+кафка из топика request_topic"""
    logger.info('auth_requests_agent started')
    async for value in stream:
        assert isinstance(value, AuthRequest), 'Не верный тип: должен быть AuthRequest'
        current_key = faust.current_event().key
        logger.info('auth_requests_agent | ключ текущего сообщения: %s', current_key)
        logger.info('auth_requests_agent | Value in faust stream: %s', value)
        logger.info('auth_requests_agent | Value as dict: %s', value.asdict())

        if not value.token:
            logger.info('auth_requests_agent | Нет токена в ивенте')
            return

        value_dict = value.asdict()

        async_verify_token = sync_to_async(UserService.verify_token, thread_sensitive=True)
        is_valid = await async_verify_token(value_dict)

        logger.info('auth_requests_agent | Валиден ли токен? -> %s', is_valid)

        if not is_valid:
            msg = {
                'id': value.id,
                'status': 'FAIL',
                'user_id': '',
                'permissions': '',
            }
            logger.error('auth_requests_agent | Токен не валиден!')
            await response_topic.send(key=value.id, value=msg)
            continue

        token = value.token
        user_id = UserService.get_user_id_from_token(token)

        # user_service = UserService(user_id)
        async_user_service = sync_to_async(UserService, thread_sensitive=True)
        user_service = await async_user_service(user_id)

        async_get_permissions = sync_to_async(user_service.get_permissions, thread_sensitive=True)
        permissions = await async_get_permissions()
        msg = {
            'id': value.id,
            'status': 'OK',
            'user_id': user_id,
            'permissions': permissions,
        }

        logger.info('auth_requests_agent | Отправка ответа: %s', msg)
        await response_topic.send(key=value.id, value=msg)


@app.agent(response_topic)
async def auth_response_agent(stream):
    """Принимает стрим из фауст+кафка из топика response_topic"""
    logger.info('auth_response_agent started')
    async for value in stream:
        logger.info('auth_response_agent | Value in faust stream: %s', value)
        logger.info('auth_response_agent | Value as dict: %s', value.asdict())
