"""
Login, Logout, TokenRefresh
"""
import logging

from django.conf import settings
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)

from apps.authorization.services.secure import (
    set_access_to_cookie,
    set_refresh_to_cookie,
    set_csrf,
    del_auth_cookies,
)


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
