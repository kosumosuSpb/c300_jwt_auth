import logging

from django.db.models import QuerySet
from django.test import Client
from rest_framework.response import Response
from rest_framework import status

from apps.authorization.models import UserData
from apps.authorization.tests.base_testcase import BaseTestCase
from apps.authorization.models.permissions import CustomPermissionModel


logger = logging.getLogger(__name__)


class TestPermissionsCreate(BaseTestCase):
    """Тесты создания CRUD-прав через представления"""
    def setUp(self) -> None:
        logger.debug('setUp | Создание объекта UserData')
        UserData.objects.create_user(
            self.email,
            self.password,
            is_superuser=True
        )
        self.client = Client()
        self.permission_name = 'some_cool_action'

    def create_permission(self) -> Response:
        """
        Делает логин под суперюзером (который указан в setUp),
        создаёт CRUD-права

        Returns:
            Response
        """
        login_response = self._login()
        # logger.debug('test_create_permission | login response: %s', response)
        logger.debug('test_create_permission | login response.content: %s',
                     login_response.content)

        data = {'name': self.permission_name}

        response: Response = self.client.post(
            self.perm_detail_url,
            data=data,
            content_type="application/json"
        )

        return response

    def test_create_permission(self):
        response = self.create_permission()
        logger.debug('test_create_permission | response: %s', response)
        logger.debug('test_create_permission | status_code: %s, response.content: %s',
                     response.status_code, response.content)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created_permissions: QuerySet = CustomPermissionModel.objects.filter(name=self.permission_name)
        logger.debug('Созданные CRUD-права в БД: %s', created_permissions)

        self.assertEqual(len(created_permissions), 4)

        actions = [perm.type for perm in created_permissions]
        self.assertEqual(len(actions), 4)

        crud_types = {'create', 'read', 'update', 'delete'}
        crud_intersection = crud_types.intersection(actions)
        self.assertEqual(len(crud_intersection), 4)

    def test_list_permission(self):
        response = self.create_permission()
        logger.debug('test_list_permission | create response: %s', response)
        logger.debug('test_list_permission | create status_code: %s, response.content: %s',
                     response.status_code, response.content)

        response = self.client.get(self.perm_list_url)
        logger.debug('test_list_permission | get list response: %s', response)
        logger.debug('test_list_permission | get list status_code: %s, response.content: %s',
                     response.status_code, response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        perms = response.json()
        self.assertEqual(len(perms), 4)

    def test_detail_permission(self):
        # TODO: дописать
        response = self.create_permission()
        logger.debug('test_detail_permission | response: %s', response)
        logger.debug('test_detail_permission | status_code: %s, response.content: %s',
                     response.status_code, response.content)
