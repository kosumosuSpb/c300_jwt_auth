import logging

import jwt
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import (
    TokenVerifyView,
    TokenObtainPairView,
    TokenRefreshView
)
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from app.authorization.user_service import UserService
from .serializers import UserSerializer
from config.settings import SIMPLE_JWT


logger = logging.getLogger(__name__)


class RegisterView(APIView):
    """Регистрация пользователей"""
    authentication_classes = []
    permission_classes = []

    def post(self, request):
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

        # token = serializer.validated_data.get('token')
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
    def post(self, request, *args, **kwargs):
        """Получает токены через супер во время логина и перемещает их в куки"""
        old_access_token = request.COOKIES.pop('access_token', None)
        old_refresh_token = request.COOKIES.pop('refresh_token', None)
        logger.debug('Tokens in request (access, refresh): %s, %s',
                     bool(old_access_token), bool(old_refresh_token))

        response: Response = super().post(request, *args, **kwargs)
        logger.debug('Response data: %s', response.data)

        access_token = response.data.pop('access', None)
        refresh_token = response.data.pop('refresh', None)

        if not all([access_token, refresh_token]):
            logger.error('Нет токенов в ответе: access: %s, refresh: %s',
                         bool(access_token), bool(refresh_token))
            return Response(
                data={'reason': 'Has not tokens in answer'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        access_cookie = {
            'key': SIMPLE_JWT['AUTH_COOKIE'],
            'value': access_token,
            'expires': SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
            'secure': SIMPLE_JWT['AUTH_COOKIE_SECURE'],
            'httponly': SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
            'samesite': SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
        }

        refresh_cookie = {
            'key': SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
            'value': refresh_token,
            'expires': SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
            'secure': SIMPLE_JWT['AUTH_COOKIE_SECURE'],
            'httponly': SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
            'samesite': SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
        }

        response.set_cookie(**access_cookie)
        response.set_cookie(**refresh_cookie)

        return response


class TokenRefreshCookieView(TokenRefreshView):
    """Класс для обновления токена доступа"""
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            logger.error('В cookies нет refresh токена для обновления токена доступа!')
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        request.data['refresh'] = refresh_token
        logger.debug('Request.data: %s', request.data)
        response = super().post(request, *args, **kwargs)

        access_token = response.data.pop('access', None)

        if not access_token:
            logger.error('В ответе нет токена доступа!')
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
