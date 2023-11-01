"""
Создание, изменение, удаление CRUD-прав через API
"""
import logging

# from django.conf import settings
from django.db.models import QuerySet
from django.http import Http404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request

from apps.authorization.models.permissions import PermissionModel
from apps.authorization.services.permissions import PermissionService
from apps.authorization.serializers import PermissionCreateSerializer, PermissionSerializer
from apps.authorization.permissions import IsSuperuser


logger = logging.getLogger(__name__)


class PermissionListView(APIView):
    """Действия над CRUD-правами"""
    permission_classes = (IsSuperuser, )

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
        operation_summary='Вывод всех CRUD-прав',
        tags=['permissions'],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description='List of all permissions',
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
    def get(self, request: Request, *args, **kwargs):
        """Вывод всех CRUD-прав"""
        logger.debug('PermissionListView - GET | request.data: %s', request.data)
        all_perms: QuerySet[PermissionModel] = PermissionModel.objects.all()
        serializer = PermissionSerializer(all_perms, many=True)

        return Response(data=serializer.data, status=status.HTTP_200_OK)

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
        operation_summary='Создание CRUD-права (состоит из 4 прав: '
                          'на чтение, запись, изменение и удаление)',
        tags=['permissions'],
        request_body=PermissionCreateSerializer,
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description='Permissions created',
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
    def post(self, request: Request, *args, **kwargs):
        """
        Создание CRUD-права.

        Создаёт 4 права по имени и описанию (не обязательно):
            на чтение, создание, обновление и удаление
        """
        logger.debug('PermissionListView - POST | request.data: %s', request.data)
        # logger.debug('PermissionListView - POST | args: %s', args)
        # logger.debug('PermissionListView - POST | kwargs: %s', kwargs)
        serializer = PermissionCreateSerializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as ve:
            logger.error('Ошибка валидации при создании CRUD-права: %s', ve)
            return Response(data='Data validation error', status=status.HTTP_400_BAD_REQUEST)

        logger.debug('PermissionListView - POST | serializer.validated_data: %s',
                     serializer.validated_data)

        perms = PermissionService.create_permissions(**serializer.validated_data)
        logger.debug('PermissionListView - POST | созданные CRUD-права: %s', perms)
        return Response(status=status.HTTP_201_CREATED)


class PermissionCreateOneView(APIView):
    """Создание одного права"""

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
        operation_summary='Создание CRUD-права (одного из 4 прав: '
                          'на чтение, запись, изменение и удаление)',
        tags=['permissions'],
        request_body=PermissionSerializer,
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description='Permissions created',
                schema=PermissionSerializer
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
    def post(self, request: Request, *args, **kwargs):
        """Создание одного права из списка: create, read, update, delete"""
        logger.debug('PermissionCreateOneView - POST | request.data: %s', request.data)

        serializer = PermissionSerializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as ve:
            logger.error('PermissionCreateOneView - POST | Ошибка валидации: %s', ve)
            return Response(data='Data validation error', status=status.HTTP_400_BAD_REQUEST)

        logger.debug('PermissionCreateOneView - POST | serializer.validated_data: %s',
                     serializer.validated_data)
        permission = PermissionService.create_one_permission(**serializer.validated_data)
        logger.debug('PermissionCreateOneView - POST | создано одно право: %s',
                     permission)

        return Response(data=serializer.validated_data, status=status.HTTP_201_CREATED)


class PermissionDetailView(APIView):
    """Действия над CRUD-правами"""
    permission_classes = (IsSuperuser, )

    def get_object(self, name: str) -> QuerySet[PermissionModel]:
        """Возвращает объекты CRUD-права"""
        perms: QuerySet = PermissionService.get_permissions(name)

        if not perms:
            msg = f'CRUD-права по имени "{name}" не найдены'
            logger.debug(msg)
            raise Http404(msg)

        return perms

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
        operation_summary='',
        tags=['permissions'],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description='Show permissions by name',
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
    def get(self, request: Request, name: str, *args, **kwargs):
        """Вывод CRUD-прав по имени"""
        logger.debug('PermissionDetailView - GET | request.data: %s', request.data)
        logger.debug('PermissionDetailView - GET | name: %s', name)
        # logger.debug('PermissionDetailView - GET | args: %s', args)
        # logger.debug('PermissionDetailView - GET | kwargs: %s', kwargs)
        perm = self.get_object(name)

        serializer = PermissionSerializer(perm, many=True)

        return Response(data=serializer.data, status=status.HTTP_200_OK)

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
        operation_summary='Редактирование CRUD-права (всех 4 прав: '
                          'на чтение, запись, изменение и удаление)',
        tags=['permissions'],
        request_body=PermissionCreateSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response(
                description='Permissions updated',
                schema=PermissionCreateSerializer
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
    def patch(self, request: Request, name: str, *args, **kwargs):
        """Редактирование CRUD-права"""
        logger.debug('PermissionDetailView - PATCH | request.data: %s', request.data)
        serializer = PermissionCreateSerializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as ve:
            logger.error('PermissionDetailView - PATCH | Ошибка валидации: %s', ve)
            return Response(data='Data validation error', status=status.HTTP_400_BAD_REQUEST)

        perms: QuerySet[PermissionModel] = PermissionService.get_permissions(name)

        logger.debug('PermissionDetailView - PATCH | perms: %s', perms)

        if not perms:
            msg = f'CRUD-права по имени "{name}" не найдены'
            logger.debug(msg)
            raise Http404(msg)

        perms.update(**serializer.validated_data)

        logger.debug('PermissionDetailView - PATCH | perms after update: %s', perms)

        return Response(status=status.HTTP_200_OK)

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
        operation_summary='Удаление CRUD-прав (всех 4 прав: '
                          'на чтение, запись, изменение и удаление)',
        tags=['permissions'],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description='Permissions deleted',
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
    def delete(self, request: Request, name: str, *args, **kwargs) -> Response:
        """Удаление CRUD-права"""
        logger.debug('PermissionDetailView - DELETE | request.data: %s', request.data)
        logger.debug('PermissionDetailView - DELETE | name: %s', name)
        # logger.debug('PermissionDetailView - DELETE | args: %s', args)
        # logger.debug('PermissionDetailView - DELETE | kwargs: %s', kwargs)
        perm = self.get_object(name)

        perm.delete()

        return Response(status=status.HTTP_200_OK)


class CreatePermissions(APIView):
    """Создание списка из многих CRUD-прав"""
    def post(self, request: Request, *args, **kwargs):
        """Создаёт много CRUD-прав по списку имён"""
        logger.debug('CreatePermissions - POST | request.data: %s', request.data)
