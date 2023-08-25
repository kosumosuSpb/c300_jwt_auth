"""
Действия с пользователем:
    - Создание (регистрация)
    - удаление
    - изменение данных
    - изменение пароля
    - активация
"""

import logging

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser

from app.authorization.models.user_data import UserData
from app.authorization.serializers import UserSerializer
from app.authorization.services.user_service import UserService

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    """Регистрация пользователей"""
    authentication_classes = []
    permission_classes = []

    def post(self, request: Request):
        logger.debug('RegisterView | POST | request data: %s', request.data)
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_validated_data: dict = serializer.validated_data
        password = user_validated_data.get('password', None)

        user: UserData = UserService.create_user(**user_validated_data)

        user.set_password(password)
        user.save()

        logger.debug('RegisterView | serializer.data: %s', serializer.data)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)


class UserDeleteView(APIView):
    """Удаление пользователя"""
    def post(self, request: Request, *args, **kwargs):
        logger.debug('UserDeleteView | POST')
        logger.debug('Удаление пользователя %s', request.user)
        eternal_delete = request.query_params.get('eternal')

        user_service = UserService(request.user)
        if eternal_delete:
            user_service.delete_user()
        else:
            user_service.mark_as_deleted()

        return Response(data={'status': 'OK'}, status=status.HTTP_200_OK)


class PasswordChangeView(APIView):
    def post(self, request: Request, *args, **kwargs):
        pass


class ManualActivateAccountView(APIView):
    """Ручная активация аккаунта"""
    permission_classes = [IsAdminUser]  # TODO: нужно дописать класс на суперпользователя?

    def post(self, request: Request, *args, **kwargs):
        logger.debug('ManualActivateAccountView | POST')
        user = request.query_params.get('user')

        if not user:
            data = {
                'status': 'ERROR',
                'detail': 'Нет атрибута "user" в параметрах адресной строки!'
                          ''}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

        user_service = UserService(user)
        user_service.manual_activate_user()

        return Response(
            data={'status': 'OK', 'detail': 'ACTIVATED'},
            status=status.HTTP_200_OK
        )


class ActivateAccountView(APIView):
    def post(self, request: Request, *args, **kwargs):
        logger.debug('ActivateAccountView')

        query_params = request.query_params
        activation_code = query_params.get('activation_code')
        user_id = query_params.get('user_id')

        if not all([activation_code, user_id]):
            return Response(
                data={
                    'status': 'BAD_REQUEST',
                    'detail': 'Не хватает кода активации, либо user_id'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user_service = UserService(user_id)
            user_service.activate_user(activation_code)
        except TypeError as te:
            return Response(data={'status': 'FAIL', 'detail': te},
                            status=status.HTTP_400_BAD_REQUEST)
        except KeyError as le:
            return Response(data={'status': 'FAIL', 'detail': le},
                            status=status.HTTP_404_NOT_FOUND)
        except ValueError as ve:
            return Response(data={'status': 'FAIL', 'detail': ve},
                            status=status.HTTP_404_NOT_FOUND)

        return Response(data={'status': 'OK'}, status=status.HTTP_202_ACCEPTED)


class TestView(APIView):
    def post(self, request: Request, *args, **kwargs):
        logger.debug('TestView | request data: %s', request.data)
        logger.debug('TestView | request COOKIES: %s', request.COOKIES)
        logger.debug('TestView | request.user: %s', request.user)
        logger.debug('TestView | request.user.type: %s', type(request.user))
        return Response(data={'status': 'OK'}, status=status.HTTP_200_OK)