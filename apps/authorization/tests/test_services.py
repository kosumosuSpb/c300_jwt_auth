import logging

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.test import override_settings

from apps.authorization.models import (
    CompanyProfile,
    Department,
    TenantProfile,
    WorkerProfile,
    UserData,
)
from apps.authorization.models import PermissionModel
from apps.authorization.services.secure import make_activation_code
from apps.authorization.services.company_service import CompanyService
from apps.authorization.services.user_service import UserService
from apps.authorization.services.permissions import PermissionService
from apps.authorization.tests.base_testcase import BaseTestCase


logger = logging.getLogger(__name__)


class TestServices(BaseTestCase):
    """Тесты основных действий со стороны сервисов"""

    @override_settings(ACTIVATION=False)
    def test_create_company(self):
        logger.debug('test_create_company')
        user_company = self._create_company()
        self.assertIsInstance(user_company, UserData)
        self.assertTrue(hasattr(user_company, 'company_profile'))
        self.assertIsInstance(user_company.company_profile, CompanyProfile)

    @override_settings(ACTIVATION=False)
    def test_create_department(self):
        user_company = self._create_company()
        profile: CompanyProfile = user_company.company_profile
        department = self._create_department(profile)
        self.assertIsInstance(department, Department)

    @override_settings(ACTIVATION=False)
    def test_create_worker_male(self):
        logger.debug('test_create_worker')
        user_worker = self._create_worker()
        self.assertIsInstance(user_worker, UserData)
        self.assertTrue(hasattr(user_worker, 'worker_profile'))
        self.assertIsInstance(user_worker.worker_profile, WorkerProfile)

    @override_settings(ACTIVATION=False)
    def test_create_worker_female(self):
        logger.debug('test_create_worker')
        user_worker = self._create_worker(sex='female')
        self.assertIsInstance(user_worker, UserData)
        self.assertTrue(hasattr(user_worker, 'worker_profile'))
        self.assertIsInstance(user_worker.worker_profile, WorkerProfile)

    @override_settings(ACTIVATION=False)
    def test_link_worker_to_department(self):
        user_worker = self._create_worker()
        user_company = self._create_company()
        dep = self._create_department(user_company.company_profile)
        CompanyService.link_worker_to_department(user_worker.worker_profile, dep)

    @override_settings(ACTIVATION=False)
    def test_create_tenant(self):
        logger.debug('test_create_tenant')
        user_tenant = self._create_tenant()
        self.assertIsInstance(user_tenant, UserData)
        self.assertTrue(hasattr(user_tenant, 'tenant_profile'))
        self.assertIsInstance(user_tenant.tenant_profile, TenantProfile)

    @override_settings(ACTIVATION=False)
    def test_create_already_created_user(self):
        logger.debug('test_register_already_registered_user')
        self._create_worker()
        with self.assertRaises(ValidationError):
            self._create_worker()

    def test_create_user_with_wrong_email(self):
        logger.debug('test_create_user_with_wrong_email')
        with self.assertRaises(ValidationError):
            self._create_tenant(email='aerg')

    def test_activation_service(self):
        """Тест активации"""
        user: UserData = UserData.objects.get(email=self.email)
        activation_code = make_activation_code()
        user.activation_code = activation_code
        user.is_active = False
        user.save()

        user_service = UserService(user)
        user_service.activate_user(activation_code)

        self.assertTrue(user.is_active)
        self.assertIsNone(user.activation_code)

    # PERMISSIONS

    def test_create_permissions_service(self):
        """Тест создания прав через сервис"""
        perms_names = ('some_permission1', 'some_permission2')
        perms_created = PermissionService.create_many_permissions(perms_names)

        self.assertTrue(isinstance(perms_created, list))
        self.assertEqual(len(perms_created), 8)

        perms_models_types = list({type(perm) for perm in perms_created})
        perms_models_type = perms_models_types[0]

        self.assertIs(perms_models_type, PermissionModel)

        names_created = {perm.name for perm in perms_created}
        intersection = names_created.intersection(perms_names)
        self.assertTrue(len(intersection), 2)

    def test_find_permissions_as_str_service(self):
        """Тест метода find_permissions класса UserService путём передачи методу строки"""
        self._create_permission()
        found_perms = UserService.find_permissions(self.permission_name)

        self.assertEqual(found_perms.count(), 4)

    def test_find_permissions_as_list_service(self):
        """Тест метода find_permissions класса UserService путём передачи методу списка"""
        perms_names = ('some_permission1', 'some_permission2')
        PermissionService.create_many_permissions(perms_names)

        found_perms = UserService.find_permissions(list(perms_names))

        self.assertEqual(found_perms.count(), 8)

    def test_find_permissions_as_tuple_service(self):
        """Тест метода find_permissions класса UserService путём передачи методу кортежа"""
        perms_names = ('some_permission1', 'some_permission2')
        PermissionService.create_many_permissions(perms_names)

        found_perms = UserService.find_permissions(perms_names)
        self.assertEqual(found_perms.count(), 8)

    def test_find_permissions_as_set_service(self):
        """Тест метода find_permissions класса UserService путём передачи методу множества"""
        perms_names = ('some_permission1', 'some_permission2')
        PermissionService.create_many_permissions(perms_names)

        found_perms = UserService.find_permissions(set(perms_names))

        self.assertEqual(found_perms.count(), 8)

    def test_find_permissions_as_queryset_service(self):
        """Тест метода find_permissions класса UserService через передачу методу QuerySet"""
        perms_names = ('some_permission1', 'some_permission2')
        perm_models = PermissionService.create_many_permissions(perms_names)
        perms_names_str_list = {perm.name for perm in perm_models}

        logger.debug('test_find_permissions_as_queryset_service | perms_names_str_list: %s',
                     perms_names_str_list)

        perm_models_qs = PermissionModel.objects.filter(name__in=perms_names_str_list)

        logger.debug('test_find_permissions_as_queryset_service | perm_models_qs: %s',
                     perm_models_qs)

        found_perms = UserService.find_permissions(perm_models_qs)

        self.assertEqual(found_perms.count(), 8)

    def test_find_permissions_wrong_names_service(self):
        """Тест метода find_permissions класса UserService путём передачи методу не верной строки"""
        perms_names = ('some_permission1', 'some_permission2')
        PermissionService.create_many_permissions(perms_names)

        with self.assertRaises(ObjectDoesNotExist):
            UserService.find_permissions('some_permission3')
