"""
Login, Logout, TokenRefresh
"""
import logging

import jwt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)

from app.authorization.services.user_service import UserService
from app.authorization.services.secure import (
    set_access_to_cookie,
    set_refresh_to_cookie,
    set_csrf,
    del_auth_cookies,
)
from app.authorization.serializers import UserSerializer
from config.settings import SIMPLE_JWT


logger = logging.getLogger(__name__)


ACCESS_TOKEN = SIMPLE_JWT.get('AUTH_COOKIE')
REFRESH_TOKEN = SIMPLE_JWT.get('AUTH_COOKIE_REFRESH')


class LoginView(TokenObtainPairView):

    def post(self, request: Request, *args, **kwargs) -> Response:
        """Получает токены через супер во время логина и перемещает их в куки"""
        logger.debug('Login | request: %s, request.data: %s', request, request.data)

        old_access_token = request.COOKIES.pop(ACCESS_TOKEN, None)
        old_refresh_token = request.COOKIES.pop(REFRESH_TOKEN, None)
        logger.debug('Login | Наличие токенов в запросе (access, refresh): %s, %s',
                     bool(old_access_token), bool(old_refresh_token))

        response: Response = super().post(request, *args, **kwargs)
        logger.debug('Login | Response data (обновлённые токены): %s',
                     response.data)

        access_token = response.data.pop('access', None)
        refresh_token = response.data.pop('refresh', None)

        if not all([access_token, refresh_token]):
            logger.error('Login | Нет токенов в ответе: access: %s, refresh: %s',
                         bool(access_token), bool(refresh_token))
            return Response(
                data={'reason': 'Has not tokens in answer'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        response = set_access_to_cookie(response, access_token)
        response = set_refresh_to_cookie(response, refresh_token)
        response = set_csrf(response, request)

        data = {'action': 'LOGIN', 'status': 'OK'}
        response.data.update(data)

        return response


class TokenRefreshCookieView(TokenRefreshView):
    """Класс для обновления токена доступа"""
    def post(self, request: Request, *args, **kwargs) -> Response:
        old_access_token = request.COOKIES.pop(ACCESS_TOKEN, None)
        logger.debug('Refresh | Наличие токена доступа в запросе: %s',
                     bool(old_access_token))
        logger.debug('Login | request.user: %s', request.user)

        refresh_token = request.COOKIES.get(REFRESH_TOKEN)

        if not refresh_token:
            logger.error('Refresh | В cookies нет refresh токена для обновления токена доступа!')
            return Response(status=status.HTTP_403_FORBIDDEN)

        request.data._mutable = True
        request.data['refresh'] = refresh_token
        logger.debug('Refresh | Request.data: %s', request.data)
        response = super().post(request, *args, **kwargs)

        new_access_token = response.data.pop('access', None)

        if SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS'):
            new_refresh_token = response.data.pop('access', None)
            if new_refresh_token:
                response = set_refresh_to_cookie(response, new_refresh_token)
            else:
                logger.error('Refresh | В ответе нет токена доступа!')
                return Response(data={'reason': 'Нет токена доступа'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not new_access_token:
            logger.error('Refresh | В ответе нет токена доступа!')
            return Response(
                data={'reason': 'Нет токена доступа'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        response = set_access_to_cookie(response, new_access_token)

        data = {'action': 'REFRESH', 'status': 'OK'}
        response.data.update(data)

        return response


class LogoutView(APIView):
    def post(self, request: Request, *args, **kwargs) -> Response:
        logger.debug('Logout')
        response = Response(
            data={'action': 'LOGOUT', 'status': 'OK'},
            status=status.HTTP_200_OK
        )
        response = del_auth_cookies(response)
        # response.cookies.clear()
        logger.debug('Response COOKIES: %s', response.cookies)

        return response
