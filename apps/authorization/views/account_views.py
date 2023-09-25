"""
Действия с пользователем:
    - Создание (регистрация)
    - удаление
    - изменение данных
    - изменение пароля
    - активация
"""

import logging

from django.conf import settings
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser

from apps.authorization.models.user_data import UserData
from apps.authorization.serializers import UserRegistrationSerializer
from apps.authorization.services.user_service import (
    UserService,
    UserServiceException,
    ActivationError
)
from apps.authorization.permissions import IsSuperuser
from apps.authorization.tasks import send_activation_mail
from apps.authorization.services.secure import make_activation_code


logger = logging.getLogger(__name__)


class RegisterView(APIView):
    """Регистрация пользователей"""
    authentication_classes = []
    permission_classes = []

    def post(self, request: Request):
        logger.debug('RegisterView | POST | request data: %s',
                     request.data)
        if 'profile' in request.data:
            logger.debug('RegisterView | POST | request data as dict: %s', dict(request.data))
            logger.debug('email: %s', request.data.get('email'))
            logger.debug('profile: %s', request.data.get('profile'))

        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_validated_data: dict = serializer.validated_data
        password = user_validated_data.get('password', None)

        logger.debug('SERIALIZER VALIDATED DATA: %s', user_validated_data)

        user: UserData = UserService.create_user(**user_validated_data)

        user.set_password(password)
        user.save()

        if settings.ACTIVATION:
            logger.debug('Включена активация, генерируем код и отправляем по почте...')
            user.is_active = False
            user.activation_code = make_activation_code()
            send_activation_mail.delay(user.pk, user.email, user.activation_code)
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
        logger.debug('PasswordChangeView | POST')


class ManualActivateAccountView(APIView):
    """Ручная активация аккаунта"""
    permission_classes = [IsAdminUser, IsSuperuser]

    def post(self, request: Request, *args, **kwargs):
        logger.debug('ManualActivateAccountView | POST')
        user_id = request.query_params.get('user_id')

        if not user_id:
            data = {
                'status': 'ERROR',
                'detail': 'Нет атрибута "user" в параметрах адресной строки!'
            }
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

        user_service = UserService(user_id)
        user_service.manual_activate_user()

        return Response(
            data={'status': 'OK', 'detail': 'ACTIVATED'},
            status=status.HTTP_200_OK
        )


class ActivateAccountView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request: Request, *args, **kwargs):
        logger.debug('ActivateAccountView')

        query_params = request.query_params
        activation_code = query_params.get('activation_code')
        user_id = query_params.get('user_id')

        if not all([activation_code, user_id]):
            msg = 'Не хватает кода активации, либо user_id'
            logger.error(msg)
            return Response(
                data={
                    'status': 'BAD_REQUEST',
                    'detail': msg
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user_service = UserService(user_id)
            user_service.activate_user(activation_code)
        except TypeError as te:
            return Response(data={'status': 'ERROR', 'detail': str(te)},
                            status=status.HTTP_400_BAD_REQUEST)
        except KeyError as le:
            return Response(data={'status': 'ERROR', 'detail': str(le)},
                            status=status.HTTP_404_NOT_FOUND)
        except ValueError as ve:
            return Response(data={'status': 'ERROR', 'detail': str(ve)},
                            status=status.HTTP_404_NOT_FOUND)
        except ActivationError as ae:
            return Response(data={'status': 'ERROR', 'detail': str(ae)},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(data={'status': 'OK'}, status=status.HTTP_202_ACCEPTED)


class TestView(APIView):

    def post(self, request: Request, *args, **kwargs):
        logger.debug('TestView | request data: %s', request.data)
        logger.debug('TestView | request COOKIES: %s', request.COOKIES)
        logger.debug('TestView | request.user: %s', request.user)
        logger.debug('TestView | request.user type: %s', type(request.user))

        return Response(data={'status': 'OK'}, status=status.HTTP_200_OK)
