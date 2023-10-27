"""
Создание, изменение, удаление CRUD-прав через API
"""
import logging

# from django.conf import settings
from django.db.models import QuerySet
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
# from drf_yasg import openapi
# from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request

from apps.authorization.models.permissions import CustomPermissionModel
from apps.authorization.serializers import PermissionCreateSerializer, PermissionSerializer
from apps.authorization.permissions import IsSuperuser


logger = logging.getLogger(__name__)


class PermissionListView(APIView):
    """Действия над CRUD-правами"""
    permission_classes = (IsSuperuser, )

    def get(self, request: Request, *args, **kwargs):
        """Вывод всех CRUD-прав"""
        logger.debug('PermissionListView - GET | request.data: %s', request.data)
        all_perms: QuerySet[CustomPermissionModel] = CustomPermissionModel.objects.all()
        serializer = PermissionSerializer(all_perms, many=True)

        return Response(data=serializer.data, status=status.HTTP_200_OK)


class PermissionDetailView(APIView):
    """Действия над CRUD-правами"""
    permission_classes = (IsSuperuser, )

    def get_object(self, name: str) -> QuerySet[CustomPermissionModel]:
        """Возвращает объекты CRUD-права"""
        try:
            perms = CustomPermissionModel.objects.filter(name=name)
        except ObjectDoesNotExist:
            logger.error('Нет права с name: %s', name)
            raise Http404

        return perms

    # TODO: дописать
    def get(self, request: Request, name: str, *args, **kwargs):
        """Вывод CRUD-прав по id"""
        logger.debug('PermissionDetailView - GET | request.data: %s', request.data)
        logger.debug('PermissionDetailView - GET | args: %s', args)
        logger.debug('PermissionDetailView - GET | kwargs: %s', kwargs)
        perm = self.get_object(name)

        serializer = PermissionSerializer(perm, many=True)

        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def post(self, request: Request, *args, **kwargs):
        """
        Создание CRUD-права.

        Создаёт 4 права по имени и описанию (не обязательно):
            на чтение, создание, обновление и удаление
        """
        logger.debug('PermissionDetailView - POST | request.data: %s', request.data)
        logger.debug('PermissionDetailView - POST | args: %s', args)
        logger.debug('PermissionDetailView - POST | kwargs: %s', kwargs)
        serializer = PermissionCreateSerializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as ve:
            logger.error('Ошибка валидации при создании CRUD-права: %s', ve)
            return Response(data='Data validation error', status=status.HTTP_400_BAD_REQUEST)

        perms = CustomPermissionModel.create_permissions(**serializer.validated_data)
        logger.debug('CreatePermissions - POST | созданные CRUD-права: %s', perms)
        return Response(status=status.HTTP_201_CREATED)

    # TODO: дописать
    def patch(self, request: Request, name: str, *args, **kwargs):
        """Редактирование CRUD-права"""
        logger.debug('PermissionDetailView - PATCH | request.data: %s', request.data)
        serializer = PermissionCreateSerializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as ve:
            logger.error('Ошибка валидации при создании CRUD-права: %s', ve)
            return Response(data='Data validation error', status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_200_OK)


class CreatePermissions(APIView):
    """Создание списка CRUD-прав"""
    def post(self, request: Request, *args, **kwargs):
        logger.debug('CreatePermissions | POST')
