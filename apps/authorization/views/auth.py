"""
Login, Logout, TokenRefresh
"""
import datetime
import logging

import jwt
from django.conf import settings
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from rest_framework_simplejwt.exceptions import TokenError

from apps.authorization.services.secure import (
    set_access_to_cookie,
    set_refresh_to_cookie,
    set_csrf,
    del_auth_cookies,
)
from apps.authorization.services.user_service import UserService


logger = logging.getLogger(__name__)


ACCESS_TOKEN = settings.SIMPLE_JWT.get('AUTH_COOKIE')
REFRESH_TOKEN = settings.SIMPLE_JWT.get('AUTH_COOKIE_REFRESH')


class LoginView(TokenObtainPairView):
    """User sign in (login)"""

    @swagger_auto_schema(
        operation_summary='User sign in (login)',
        tags=['auth'],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description='Get JWT (access, refresh) in cookie',
            ),
            status.HTTP_401_UNAUTHORIZED: openapi.Response(
                description='No active account found with the given credentials',
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Response(
                description='Has not tokens in answer',
            )
        }
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        logger.debug('Login | request: %s, request.data: %s', request, request.data)

        old_access_token = request.COOKIES.pop(ACCESS_TOKEN, None)
        old_refresh_token = request.COOKIES.pop(REFRESH_TOKEN, None)
        logger.debug('Login | Наличие токенов в запросе (access, refresh): %s, %s',
                     bool(old_access_token), bool(old_refresh_token))

        response: Response = super().post(request, *args, **kwargs)
        logger.debug('Login | Response data (новые токены): %s',
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
    """Get new access token"""

    @swagger_auto_schema(
        operation_summary='Get new access token',
        tags=['auth'],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description='Get JWT (new access) in cookie',
            ),
            status.HTTP_401_UNAUTHORIZED: openapi.Response(
                description='No valid token found in cookie "refresh_token"',
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Response(
                description='Has not tokens in answer',
            )
        }
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        old_access_token = request.COOKIES.pop(ACCESS_TOKEN, None)
        logger.debug('Refresh | Наличие токена доступа в запросе: %s',
                     bool(old_access_token))
        logger.debug('Login | request.user: %s', request.user)

        refresh_token = request.COOKIES.get(REFRESH_TOKEN)

        if not refresh_token:
            logger.error('Refresh | В cookies нет refresh токена для обновления токена доступа!')
            return Response(data={'reason': 'Нет токена обновления!'}, status=status.HTTP_403_FORBIDDEN)

        # тесты без этого падают, потому что не дают делать изменения в Request
        if hasattr(request.data, '_mutable'):
            request.data._mutable = True

        request.data['refresh'] = refresh_token
        logger.debug('Refresh | Пришло: Request.data: %s', request.data)
        response = super().post(request, *args, **kwargs)

        logger.debug('Refresh | Ответ от simplejwt: Response.data: %s', response.data)
        new_access_token = response.data.pop('access', None)

        if settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS'):
            new_refresh_token = response.data.pop('refresh', None)
            if new_refresh_token:
                response = set_refresh_to_cookie(response, new_refresh_token)
            else:
                logger.error('Refresh | В ответе нет токена обновления!')
                return Response(data={'reason': 'Нет токена обновления'},
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


class TokenVerifyAuthView(TokenVerifyView):
    """Верифицирует токен и возвращает пользователя"""

    @swagger_auto_schema(
        operation_summary='Token verification',
        tags=['auth'],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description='Token verification success',
                examples={
                    'application/json': {
                        "status": "OK",
                        "user_id": 1,
                        "permissions": {
                            "is_superuser": False,
                            "is_staff": False,
                            "is_active": True,
                            "is_admin": False,
                            "is_deleted": False
                        }
                    }
                }
            ),
            status.HTTP_401_UNAUTHORIZED: openapi.Response(
                description='Invalid access token',
                examples={
                    'application/json': {
                        "status": "FAIL",
                        "user_id": '',
                        "permissions": ''
                    }
                }
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description='No token found in request',
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Response(
                description='Server error',
            )
        }
    )
    def post(self, request: Request, *args, **kwargs):
        logger.debug('TokenVerifyAuthView - POST | request data: %s', request.data)
        token_from_cookies = request.COOKIES.get('access_token')
        logger.debug('TokenVerifyAuthView - POST | наличие токена в куках: %s',
                     token_from_cookies)

        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            logger.error('Ошибка валидации токена: %s', e)
            # raise InvalidToken(e.args[0])
            return Response(data='Invalid token', status=status.HTTP_401_UNAUTHORIZED)

        # token = serializer.validated_data.get('token')
        token = request.data.get('token')
        logger.debug('serializer.validated_data: %s', serializer.validated_data)
        if not token:
            logger.error('Токен не найден!')
            # raise InvalidToken('Нет токена в запросе')
            return Response(data='Token cannot be blank', status=status.HTTP_400_BAD_REQUEST)

        logger.debug('Одинаковы ли токены в куках и в теле запроса: %s',
                     token == token_from_cookies)

        algorythm = settings.SIMPLE_JWT.get('ALGORITHM')
        secret_key = settings.SIMPLE_JWT.get('SIGNING_KEY')
        payload: dict = jwt.decode(token, secret_key, algorithms=[algorythm, ])
        logger.debug('PAYLOAD: %s', payload)

        date_exp = payload.get('exp')
        user_id = payload.get('user_id')

        if not date_exp:
            logger.error('Не верный формат пейлоада: нет даты истечения токена!')
            return Response(
                data='Invalid payload format: there are no token expired date!',
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        if not user_id:
            logger.error('Не верный формат пейлоада: нет user_id!')
            return Response(
                data='Invalid payload format: there are no user id!',
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        logger.debug(
            'id пользователя: %s, дата истечения токена: %s',
            user_id, datetime.datetime.fromtimestamp(date_exp)
                     )

        user_service: UserService = UserService(user_id)
        permissions = user_service.get_permissions()

        answer = {
            'status': 'OK',
            'user_id': user_id,
            'permissions': permissions,
        }

        return Response(answer, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """User logout"""

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name='X-CSRFToken',
                in_=openapi.IN_HEADER,
                type=openapi.TYPE_STRING,
                description='CSRF token',
                required=True,
            ),
        ],
        operation_summary='User logout',
        tags=['auth'],
        responses={
            status.HTTP_204_NO_CONTENT: openapi.Response(
                description='No Content',
            ),
            status.HTTP_401_UNAUTHORIZED: openapi.Response(
                description='Authentication credentials were not provided',
            ),
            status.HTTP_403_FORBIDDEN: openapi.Response(
                description='CSRF Failed: CSRF token missing, '
                            'CSRF Failed: CSRF token from the "X-Csrftoken" HTTP header incorrect',
            ),
        }
    )
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
