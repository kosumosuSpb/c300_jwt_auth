import logging

import jwt
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework_simplejwt.views import TokenVerifyView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import Token

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



