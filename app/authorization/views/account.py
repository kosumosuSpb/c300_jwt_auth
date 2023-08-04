"""
Действия с пользователем: Создание, удаление, изменение данных, изменение пароля
"""
import logging

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app.authorization.serializers import UserSerializer
from app.authorization.services.user_service import UserService

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


class UserDeleteView(APIView):
    """Удаление пользователя"""
    def post(self, request: Request, *args, **kwargs):
        logger.debug('UserDeleteView | POST')
        logger.debug('Удаление пользователя %s', request.user)
        user_service = UserService(request.user)
        status = user_service.del_user()
        logger.debug('Статус операции удаления пользователя: %s', status)


class PasswordChangeView(APIView):
    def post(self, request: Request, *args, **kwargs):
        pass


class ActivateAccountView(APIView):
    def post(self, request: Request, *args, **kwargs):
        pass


class TestView(APIView):
    def post(self, request: Request, *args, **kwargs):
        logger.debug('TestView | request data: %s', request.data)
        logger.debug('TestView | request COOKIES: %s', request.COOKIES)
        logger.debug('TestView | request.user: %s', request.user)
        logger.debug('TestView | request.user.type: %s', type(request.user))
        return Response(data={'status': 'OK'}, status=status.HTTP_200_OK)
