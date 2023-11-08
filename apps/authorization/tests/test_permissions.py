import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet
from django.test import Client
from rest_framework.response import Response
from rest_framework import status

from apps.authorization.models import UserData
from apps.authorization.services.user_service import UserService
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
        создаёт CRUD-права через представление

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

    def create_one_permission(self, name: str | None = None, action: str | None = None) -> Response:
        """
        Делает логин под суперюзером (который указан в setUp),
        создаёт CRUD-право (одно)

        Returns:
            Response
        """
        login_response = self._login()
        # logger.debug('create_permission | login response: %s', response)
        logger.debug('create_permission | login response.content: %s',
                     login_response.content)

        permission_name = name or self.permission_name
        action = action or 'create'

        data = {
            'name': permission_name,
            'action': action,
        }

        response: Response = self.client.post(
            self.perms_one_url,
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

        actions = [perm.action for perm in created_permissions]
        self.assertEqual(len(actions), 4)

        crud_types = {action.lower() for action in PermissionModel.ACTIONS}
        crud_intersection = crud_types.intersection(actions)
        self.assertEqual(len(crud_intersection), 4)

    def test_create_one_permission(self):
        action = 'create'
        response = self.create_one_permission(action=action)
        logger.debug('test_create_one_permission | response: %s', response)
        logger.debug('test_create_one_permission | status_code: %s, response.content: %s',
                     response.status_code, response.content)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        try:
            created_permission: PermissionModel = PermissionModel.objects.get(name=self.permission_name)
            logger.debug('test_create_one_permission | Созданное CRUD-право в БД: %s',
                         created_permission)
        except ObjectDoesNotExist as dne:
            logger.error('test_create_one_permission | право не найдено: %s', dne)
            raise AssertionError(f'Ошибка при поиске созданного права: {dne}')

        self.assertEqual(created_permission.action, action)
        self.assertEqual(created_permission.name, self.permission_name)

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

    def test_add_permission_to_company_as_list(self):
        """Добавление прав компании. Право передаётся списком"""
        self._login()

        company_user = self._create_company()
        self.create_permission()

        data = {
            'permissions': [self.permission_name, ],
        }

        response = self.client.patch(
            self.perms_grant_url + str(company_user.pk) + '/',
            data=data,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        company_user.refresh_from_db()
        all_perms = company_user.all_permissions
        actual_perms = [perm for perm in all_perms if perm.name == self.permission_name]

        self.assertEqual(len(actual_perms), 4)

    def test_add_permissions_to_company(self):
        """Добавление нескольких прав компании. Права передаются списком или кортежем"""
        perms_names = ('some_permission1', 'some_permission2')

        self._create_permissions(perms_names)

        self._login()
        company_user = self._create_company()

        data = {
            'permissions': perms_names,
        }

        response = self.client.patch(
            self.perms_grant_url + str(company_user.pk) + '/',
            data=data,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        company_user.refresh_from_db()
        all_perms = company_user.all_permissions
        actual_perms = [perm for perm in all_perms if perm.name in perms_names]

        self.assertEqual(len(actual_perms), 8)

    def test_add_permission_to_company_as_str(self):
        """Добавление прав компании. Право передаётся одной строкой"""
        self._login()

        company_user = self._create_company()
        self.create_permission()

        data = {
            'permissions': self.permission_name,
        }

        response = self.client.patch(
            self.perms_grant_url + str(company_user.pk) + '/',
            data=data,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        company_user.refresh_from_db()
        all_perms = company_user.all_permissions
        actual_perms = [perm for perm in all_perms if perm.name == self.permission_name]

        self.assertEqual(len(actual_perms), 4)

    def test_add_wrong_permission(self):
        """Добавление прав компании. Право передаётся одной строкой"""
        self._login()

        company_user = self._create_company()
        self.create_permission()

        data = {
            'permissions': 'wrong_permission',
        }

        response = self.client.patch(
            self.perms_grant_url + str(company_user.pk) + '/',
            data=data,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_equal_permissions_to_company_and_to_worker(self):
        """Добавление одних и тех же прав компании и сотруднику"""
        company_user, department, worker_user = self._create_company_and_worker(as_tuple=True)

        # logger.debug('worker department: %s', worker_user.worker_profile.department)

        perms_names = ('some_permission1', 'some_permission2')
        self._create_permissions(perms_names)

        company_user_service = UserService(company_user)
        company_user_service.add_permissions(perms_names)

        self._login()

        data = {
            'permissions': perms_names,
        }

        response = self.client.patch(
            self.perms_grant_url + str(worker_user.pk) + '/',
            data=data,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        worker_user.refresh_from_db()
        all_perms = worker_user.all_permissions
        actual_perms = [perm for perm in all_perms if perm.name in perms_names]

        self.assertEqual(len(actual_perms), 8)

    def test_add_different_permissions_to_company_and_to_worker(self):
        """Добавление разных прав компании и сотруднику"""
        company_user, department, worker_user = self._create_company_and_worker(as_tuple=True)

        # logger.debug('worker department: %s', worker_user.worker_profile.department)

        perms_names1 = ('some_permission1', 'some_permission2')
        perms_names2 = ('some_permission3', 'some_permission4')
        self._create_permissions(perms_names1 + perms_names2)

        company_user_service = UserService(company_user)
        company_user_service.add_permissions(perms_names1)

        self._login()

        data = {
            'permissions': perms_names2,
        }

        response = self.client.patch(
            self.perms_grant_url + str(worker_user.pk) + '/',
            data=data,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        worker_user.refresh_from_db()
        all_perms = worker_user.all_permissions
        actual_perms = [perm for perm in all_perms if perm.name in perms_names2]

        self.assertEqual(len(actual_perms), 0)

    def test_add_intersection_permissions_to_company_and_to_worker(self):
        """
        Добавление прав компании и сотруднику. Часть выдаваемых прав компании и сотруднику - общие
        """
        company_user, department, worker_user = self._create_company_and_worker(as_tuple=True)

        # logger.debug('worker department: %s', worker_user.worker_profile.department)

        perms_names1 = ('some_permission1', 'some_permission2')
        perms_names2 = ('some_permission2', 'some_permission3')
        self._create_permissions(perms_names1 + perms_names2)

        company_user_service = UserService(company_user)
        company_user_service.add_permissions(perms_names1)

        self._login()

        data = {
            'permissions': perms_names2,
        }

        response = self.client.patch(
            self.perms_grant_url + str(worker_user.pk) + '/',
            data=data,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        worker_user.refresh_from_db()
        all_perms = worker_user.all_permissions
        actual_perms = [perm for perm in all_perms if perm.name in perms_names2]

        self.assertEqual(len(actual_perms), 4)

    def test_user_delete_permissions(self):
        """Удаление прав у пользователя"""
        company_user = self._create_company()
        perms_names = ('some_permission1', 'some_permission2')
        perm_models = self._create_permissions(perms_names)

        company_user_service = UserService(company_user)
        company_user_service.add_permissions(perm_models)

        data = {
            'permissions': perms_names[0],
        }

        self._login()
        response = self.client.delete(
            self.perms_grant_url + str(company_user.pk) + '/',
            data=data,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        company_user.refresh_from_db()
        all_perms = company_user.all_permissions

        actual_perms = [perm for perm in all_perms if perm.name in perms_names]

        self.assertEqual(len(actual_perms), 4)
        self.assertEqual(actual_perms[0].name, perms_names[1])
