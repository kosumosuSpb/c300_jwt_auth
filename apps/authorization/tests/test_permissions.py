import logging

from django.db.models import QuerySet
from django.test import Client
from rest_framework.response import Response
from rest_framework import status

from apps.authorization.models import UserData
from apps.authorization.tests.base_testcase import BaseTestCase
from apps.authorization.models.permissions import PermissionModel


logger = logging.getLogger(__name__)


class TestPermissions(BaseTestCase):
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

    # def tearDown(self) -> None:
    #     logger.debug('tearDown | Удаление тестового пользователя UserData')
    #     try:
    #         user: UserData = UserData.objects.get(email=self.email)
    #     except ObjectDoesNotExist as e:
    #         logger.debug('Пользователь %s не найден (%s)', self.email, e)
    #     else:
    #         logger.debug('Пользователь %s найден, удаляем', self.email)
    #         user.delete()

    def create_permission(self, name: str | None = None) -> Response:
        """
        Делает логин под суперюзером (который указан в setUp),
        создаёт CRUD-права

        Returns:
            Response
        """
        login_response = self._login()
        # logger.debug('create_permission | login response: %s', response)
        logger.debug('create_permission | login response.content: %s',
                     login_response.content)

        permission_name = name or self.permission_name

        data = {'name': permission_name}

        response: Response = self.client.post(
            self.perms_url,
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

        created_permissions: QuerySet = PermissionModel.objects.filter(name=self.permission_name)
        logger.debug('Созданные CRUD-права в БД: %s', created_permissions)

        self.assertEqual(len(created_permissions), 4)

        actions = [perm.type for perm in created_permissions]
        self.assertEqual(len(actions), 4)

        crud_types = {action.lower() for action in PermissionModel.ACTIONS}
        crud_intersection = crud_types.intersection(actions)
        self.assertEqual(len(crud_intersection), 4)

    def test_list_permission(self):
        response = self.create_permission()
        response = self.create_permission('another_perm_name')
        logger.debug('test_list_permission | create response: %s', response)
        logger.debug('test_list_permission | create status_code: %s, response.content: %s',
                     response.status_code, response.content)

        response = self.client.get(self.perms_url)

        logger.debug('test_list_permission | get list response: %s', response)
        logger.debug('test_list_permission | get list status_code: %s, response.content: %s',
                     response.status_code, response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        perms = response.json()
        self.assertEqual(len(perms), 8)

    def test_get_permission(self):
        response = self.create_permission()
        logger.debug('test_get_permission | response: %s', response)
        logger.debug('test_get_permission | status_code: %s, response.content: %s',
                     response.status_code, response.content)

        response = self.client.get(self.perms_url + self.permission_name + '/')

        logger.debug('test_get_permission | get list response: %s', response)
        logger.debug('test_get_permission | get list status_code: %s, response.content: %s',
                     response.status_code, response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        perms = response.json()
        self.assertEqual(len(perms), 4)

    def test_delete_permission(self):
        response = self.create_permission()
        logger.debug('test_delete_permission | response: %s', response)
        logger.debug('test_delete_permission | status_code: %s, response.content: %s',
                     response.status_code, response.content)

        response = self.client.delete(self.perms_url + self.permission_name + '/')

        logger.debug('test_delete_permission | get list response: %s', response)
        logger.debug('test_delete_permission | get list status_code: %s, response.content: %s',
                     response.status_code, response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        perms = PermissionModel.objects.filter(name=self.permission_name)

        self.assertEqual(len(perms), 0)

    def test_patch_permission(self):
        response = self.create_permission()
        logger.debug('test_patch_permission | create response: %s', response)
        logger.debug('test_patch_permission | create status_code: %s, response.content: %s',
                     response.status_code, response.content)

        new_perm_name = 'some_another_cool_name'
        new_description = 'May'

        data = {
            'name': new_perm_name,
            'description': new_description
        }

        response = self.client.patch(
            self.perms_url + self.permission_name + '/',
            data=data,
            content_type="application/json"
        )

        logger.debug('test_patch_permission | patch response: %s', response)
        logger.debug('test_patch_permission | patch status_code: %s, response.content: %s',
                     response.status_code, response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        perms: QuerySet[PermissionModel] = PermissionModel.objects.filter(name=new_perm_name)
        old_perms: QuerySet[PermissionModel] = PermissionModel.objects.filter(name=self.permission_name)

        logger.debug('test_patch_permission | old_perms found: %s', old_perms)
        logger.debug('test_patch_permission | perms found: %s', perms)
        logger.debug('test_patch_permission | perms[0] found description: %s',
                     perms[0].description)

        self.assertEqual(len(perms), 4)
        self.assertEqual(len(old_perms), 0)

        self.assertEqual(new_description, perms[0].description)
