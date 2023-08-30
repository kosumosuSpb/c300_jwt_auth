import logging
import secrets

from django.middleware import csrf
from rest_framework.response import Response
from rest_framework.request import Request

from config.settings import SIMPLE_JWT, CSRF_COOKIE_NAME


logger = logging.getLogger(__name__)


def set_access_to_cookie(response: Response, access_token: str) -> Response:
    """Устанавливает токен доступа в куки Response"""
    logger.debug('set_access_to_cookie')
    if access_token is None:
        logger.warning('Токен доступа равен None! Скорее всего что-то пошло не так')

    access_cookie = {
        'key': SIMPLE_JWT['AUTH_COOKIE'],
        'value': access_token,
        'expires': SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
        'secure': SIMPLE_JWT['AUTH_COOKIE_SECURE'],
        'httponly': SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
        'samesite': SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
    }
    response.set_cookie(**access_cookie)
    return response


def set_refresh_to_cookie(response: Response, refresh_token: str) -> Response:
    """Устанавливает токен обновления в куки Response"""
    logger.debug('set_refresh_to_cookie')
    if refresh_token is None:
        logger.warning('Токен обновления равен None! Скорее всего что-то пошло не так')

    refresh_cookie = {
        'key': SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
        'value': refresh_token,
        'expires': SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
        'secure': SIMPLE_JWT['AUTH_COOKIE_SECURE'],
        'httponly': SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
        'samesite': SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
    }
    response.set_cookie(**refresh_cookie)
    return response


def set_csrf(response: Response, request: Request) -> Response:
    """Генерация и установка CSRF токена в cookies объекта Response"""
    logger.debug('set_csrf')

    csrf_token = csrf.get_token(request)

    csrf_cookie = {
        'key': CSRF_COOKIE_NAME,
        'value': csrf_token,
        'secure': False,
        'httponly': False,
        'samesite': 'Lax',
    }

    response.set_cookie(**csrf_cookie)

    return response


def del_auth_cookies(response: Response, delete_csrf=True) -> Response:
    logger.debug('delete_auth_cookies')
    response.delete_cookie(
        SIMPLE_JWT['AUTH_COOKIE'],
        domain=SIMPLE_JWT['AUTH_COOKIE_DOMAIN'],
        path=SIMPLE_JWT['AUTH_COOKIE_PATH']
    )
    response.delete_cookie(
        SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
        domain=SIMPLE_JWT['AUTH_COOKIE_DOMAIN'],
        path=SIMPLE_JWT['AUTH_COOKIE_PATH']
    )

    if delete_csrf:
        response.delete_cookie(
            CSRF_COOKIE_NAME,
            domain=None,
            path='/'
        )

    # TODO: нужно добавлять токены в блок

    return response


def make_activation_code(length: int | None = None) -> str:
    """Создание кода активации"""
    code = secrets.token_hex(length // 2)
    logger.debug('Сгенерирован код активации: %s', code)
    return code
