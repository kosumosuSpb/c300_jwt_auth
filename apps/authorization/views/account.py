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
from django.core.exceptions import ObjectDoesNotExist
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser

from apps.authorization.models.user_data import UserData
from apps.authorization.serializers import UserRegistrationSerializer
from apps.authorization.services.user_service import (
    UserService,
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

    @swagger_auto_schema(
        request_body=UserRegistrationSerializer,
        operation_summary='Регистрация нового пользователя',
        tags=['account'],
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description='Пользователь создан',
                schema=UserRegistrationSerializer,
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description='Invalid data'
            )
        }
    )
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
        password = user_validated_data.get('password')

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
    permission_classes = [IsSuperuser | IsAdminUser]

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
        operation_summary='User delete',
        tags=['account'],
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
            status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Response(
                description='Internal server error',
            )
        }
    )
    def delete(self, request: Request, user_id: int, *args, **kwargs):
        logger.debug('UserDeleteView | DELETE')

        logger.debug('UserDeleteView | DELETE | request.data: %s', request.data)
        logger.debug('UserDeleteView | DELETE | пришёл user_id: %s', user_id)

        user_service = UserService(user_id)
        user_service.delete_user()

        return Response(data={'status': 'OK'}, status=status.HTTP_204_NO_CONTENT)

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
        operation_summary='User mark as deleted',
        tags=['account'],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description='No Content',
            ),
            status.HTTP_401_UNAUTHORIZED: openapi.Response(
                description='Authentication credentials were not provided',
            ),
            status.HTTP_403_FORBIDDEN: openapi.Response(
                description='CSRF Failed: CSRF token missing, '
                            'CSRF Failed: CSRF token from the "X-Csrftoken" HTTP header incorrect',
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Response(
                description='Internal server error',
            )
        }
    )
    def patch(self, request: Request, user_id: int, *args, **kwargs):
        """Помечает пользователя как удалённого, но не удаляет его"""
        logger.debug('UserDeleteView | PATCH')

        logger.debug('UserDeleteView | PATCH | request.data: %s', request.data)
        logger.debug('UserDeleteView | PATCH | пришёл user_id: %s', user_id)

        user_service = UserService(user_id)
        user_service.mark_as_deleted()

        return Response(data={'status': 'OK'}, status=status.HTTP_200_OK)


class PasswordChangeView(APIView):
    """Изменение пароля"""

    @swagger_auto_schema(
        tags=['account'],
    )
    def post(self, request: Request, *args, **kwargs):
        logger.debug('PasswordChangeView | POST')


# TODO: дописать
class UserProfileDetailView(APIView):
    """Изменение профиля пользователя"""

    def get(self, request: Request, user_id: int):
        """Просмотр профиля пользователя"""
        logger.debug('UserProfileDetailView - GET | request.data: %s', request.data)
        logger.debug('UserProfileDetailView - GET | user_id: %s', user_id)

        try:
            user: UserData = UserData.objects.select_related(
                'company_profile', 'worker_profile', 'tenant_profile'
            ).get(pk=user_id)
            logger.debug('UserProfileDetailView - GET | user_data: %s', user)
            logger.debug('UserProfileDetailView - GET | user_data.profile: %s', user.profile)
        except ObjectDoesNotExist as dne:
            msg = f'Пользователь {user_id} не найден: {dne}'
            logger.error(msg)
            return Response(data=msg, status=status.HTTP_404_NOT_FOUND)

        serializer = UserRegistrationSerializer(user)

        logger.debug('UserProfileDetailView - GET | serializer.data: %s', serializer.data)

        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def put(self, request: Request, user_id: int, *args, **kwargs):
        """Полное редактирование профиля пользователя"""
        logger.debug('UserProfileDetailView - PUT | request.data: %s', request.data)


class ManualActivateAccountView(APIView):
    """Ручная активация аккаунта"""
    permission_classes = [IsSuperuser | IsAdminUser]

    @swagger_auto_schema(
        tags=['account'],
    )
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
    """Активация аккаунта"""
    authentication_classes = []
    permission_classes = []

    @swagger_auto_schema(
        tags=['account'],
    )
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
    """Тестовый эндпоинт с включённым CSRF"""

    @swagger_auto_schema(
        tags=['account'],
    )
    def post(self, request: Request, *args, **kwargs):
        logger.debug('TestView | request data: %s', request.data)
        logger.debug('TestView | request COOKIES: %s', request.COOKIES)
        logger.debug('TestView | request.user: %s', request.user)
        logger.debug('TestView | request.user type: %s', type(request.user))

        return Response(data={'status': 'OK'}, status=status.HTTP_200_OK)
