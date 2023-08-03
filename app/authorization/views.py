import logging

import jwt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from rest_framework_simplejwt.views import (
    TokenVerifyView,
    TokenObtainPairView,
    TokenRefreshView
)
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from app.authorization.user_service import UserService
from app.authorization.authentication import CookiesJWTAuthentication
from .serializers import UserSerializer
from config.settings import SIMPLE_JWT, CSRF_COOKIE_NAME
from app.authorization.services.secure import (
    set_access_to_cookie,
    set_refresh_to_cookie,
    set_csrf,
    del_auth_cookies,
)


logger = logging.getLogger(__name__)


class RegisterView(APIView):
    """Регистрация пользователей"""
    authentication_classes = []
    permission_classes = []

    def post(self, request: Request):
        logger.debug('RegisterView - POST - request data: %s', request.data)
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class TokenVerifyAuthView(TokenVerifyView):
    """Верифицирует токен и возвращает пользователя"""
    def post(self, request, *args, **kwargs):
        logger.debug('TokenVerifyAuthView - POST - request data: %s', request.data)

        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        token = request.data.get('token')
        logger.debug('serializer.validated_data: %s', serializer.validated_data)
        if not token:
            raise InvalidToken('Нет токена в запросе')

        algorythm = SIMPLE_JWT.get('ALGORITHM')
        secret_key = SIMPLE_JWT.get('SIGNING_KEY')
        payload = jwt.decode(token, secret_key, algorithms=[algorythm, ])
        logger.debug('PAYLOAD: %s', payload)

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class LoginView(TokenObtainPairView):

    def post(self, request: Request, *args, **kwargs):
        """Получает токены через супер во время логина и перемещает их в куки"""
        logger.debug('Login | request: %s, request.data: %s', request, request.data)

        old_access_token = request.COOKIES.pop('access_token', None)
        old_refresh_token = request.COOKIES.pop('refresh_token', None)
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

        access_changed = old_access_token != access_token
        refresh_changed = old_refresh_token != refresh_token
        if not all([access_changed, refresh_changed]):
            logger.error('Не изменился один из токенов! '
                         'Access изменился: %s, Refresh изменился: %s',
                         access_changed, refresh_changed)
            return Response(
                data={'reason': 'Токены не обновились'},
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
    def post(self, request: Request, *args, **kwargs):
        old_access_token = request.COOKIES.pop('access_token', None)
        logger.debug('Refresh | Наличие токена доступа в запросе: %s',
                     bool(old_access_token))

        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            logger.error('Refresh | В cookies нет refresh токена для обновления токена доступа!')
            return Response(status=status.HTTP_403_FORBIDDEN)

        request.data['refresh'] = refresh_token
        logger.debug('Refresh | Request.data: %s', request.data)
        response = super().post(request, *args, **kwargs)

        access_token = response.data.pop('access', None)

        if not access_token:
            logger.error('Refresh | В ответе нет токена доступа!')
            return Response(data={'reason': 'Нет токена доступа'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if old_access_token == access_token:
            logger.error('Refresh | Токен не обновился!')
            return Response(data={'reason': 'Токен не обновился'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response = set_access_to_cookie(response, access_token)

        data = {'action': 'REFRESH', 'status': 'OK'}
        response.data.update(data)

        return response


class LogoutView(APIView):
    def post(self, request: Request, *args, **kwargs):
        logger.debug('Logout')
        response = Response(
            data={'action': 'LOGOUT', 'status': 'OK'},
            status=status.HTTP_200_OK
        )
        response = del_auth_cookies(response)
        # response.cookies.clear()
        logger.debug('Response COOKIES: %s', response.cookies)

        return response


class AccountDeleteView(APIView):
    def post(self, request: Request, *args, **kwargs):
        pass


class PasswordChangeView(APIView):
    def post(self, request: Request, *args, **kwargs):
        pass


class ActivateAccountView(APIView):
    def post(self, request: Request, *args, **kwargs):
        pass


class TestView(APIView):
    # authentication_classes = []
    # permission_classes = []

    def post(self, request: Request, *args, **kwargs):
        return Response(data={'status': 'OK'}, status=status.HTTP_200_OK)
