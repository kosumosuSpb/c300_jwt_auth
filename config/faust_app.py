import logging
import os
import json

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

import faust
from asgiref.sync import sync_to_async
from django.conf import settings
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from rest_framework.exceptions import ValidationError

from apps.authorization.services.user_service import UserService


logger = logging.getLogger(__name__)


AUTH_REQUEST = 'auth_request'
AUTH_RESPONSE = 'auth_response'


class KafkaSender:
    """Простой класс для отправки сообщений в кафку"""
    def __init__(self, kafka_servers: list[str] | None = None):
        self.servers = self._cut_url_string(kafka_servers)
        self.producer = self._get_producer()

    def _get_producer(self):
        try:
            kafka_producer = KafkaProducer(
                bootstrap_servers=self.servers,
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
        except NoBrokersAvailable as e:
            logger.error('Kafka Broker Error: %s', e)
            logger.error('Servers in args: %s', self.servers)
            logger.error('settings.KAFKA_URL: %s', settings.KAFKA_URL)
            raise
        return kafka_producer

    @staticmethod
    def _cut_url_string(servers: list[str]):
        """Убирает kafka:// перед серверами"""
        new_servers = list(map(lambda server: server.replace('kafka://', ''), servers))
        return new_servers

    def send(self, message, topic: str):
        """Отправка сообщения в топик"""
        self.producer.send(topic, value=message)


sender = KafkaSender([settings.KAFKA_URL, ])

app = faust.App(
    'auth_bus',
    broker=settings.KAFKA_URL,
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
                'status': 'FAIL',
                'user_id': '',
                'permissions': '',
            }
            logger.error('auth_requests_agent | Токен не валиден!')
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

        logger.info('auth_requests_agent | Отправка ответа: %s', msg)
        sender.send(msg, AUTH_RESPONSE)


@app.agent(response_topic)
async def auth_response_agent(stream):
    """Принимает стрим из фауст+кафка из топика response_topic"""
    logger.info('auth_response_agent started')
    async for value in stream:
        logger.info('auth_response_agent | Value in faust stream: %s', value)
        logger.info('auth_response_agent | Value as dict: %s', value.asdict())
