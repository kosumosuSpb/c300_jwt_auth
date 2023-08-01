import logging
import os
import json

import django
import faust
from asgiref.sync import sync_to_async
from kafka import KafkaProducer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from config.settings import KAFKA_URL
from app.authorization.user_service import UserService


logger = logging.getLogger(__name__)


AUTH_REQUEST = 'auth_request'
AUTH_RESPONSE = 'auth_response'


class KafkaSender:
    """Простой класс для отправки сообщений в кафку"""
    def __init__(self, kafka_servers: list[str] | None = None):
        self.servers = self._repair_servers(kafka_servers)
        self.producer = self._get_producer()

    def _get_producer(self):
        return KafkaProducer(
            bootstrap_servers=self.servers,
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )

    @staticmethod
    def _repair_servers(servers: list[str]):
        """Убирает kafka:// перед серверами"""
        new_servers = list(map(lambda server: server.replace('kafka://', ''), servers))
        return new_servers

    def send(self, message, topic: str):
        """Отправка сообщения в топик"""
        self.producer.send(topic, value=message)


sender = KafkaSender([KAFKA_URL, ])

app = faust.App(
    'auth_bus',
    broker=KAFKA_URL,
    # store='rocksdb://'
    autodiscovery=True,
)


class AuthRequest(faust.Record):
    token: str


class AuthResponse(faust.Record):
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
async def auth_requests_agent(stream):
    """Принимает стрим из фауст+кафка из топика request_topic"""
    logger.info('auth_requests_agent started')
    async for value in stream:
        assert isinstance(value, AuthRequest), 'Не верный тип: должен быть AuthRequest'
        logger.info('Value in faust stream: %s', value)
        logger.info('Value as dict: %s', value.asdict())

        if not value.token:
            logger.info('Нет токена в ивенте')
            return

        value_dict = value.asdict()
        is_valid = UserService.verify_token(value_dict)
        logger.info('Валиден ли токен? -> %s', is_valid)

        if not is_valid:
            msg = {
                'status': 'FAIL',
                'user_id': '',
                'permissions': '',
            }
            logger.error('Токен не валиден!')
            sender.send(msg, AUTH_RESPONSE)
            return

        token = value.token
        user_id = UserService.get_user_id_from_token(token)

        # user_service = UserService(user_id)
        get_user_service = sync_to_async(UserService, thread_sensitive=True)
        user_service = await get_user_service(user_id)

        async_get_permissions = sync_to_async(user_service.get_permissions, thread_sensitive=True)
        permissions = await async_get_permissions()
        msg = {
            'status': 'OK',
            'user_id': user_id,
            'permissions': permissions,
        }

        sender.send(msg, AUTH_RESPONSE)


@app.agent(response_topic)
async def auth_response_agent(stream):
    """Принимает стрим из фауст+кафка из топика response_topic"""
    logger.info('auth_response_agent started')
    async for value in stream:
        logger.info('auth_response_agent: Value in faust stream: %s', value)
