import logging

from django.core.exceptions import ValidationError
from django.test import override_settings

from apps.authorization.models import (
    CompanyProfile,
    Department,
    TenantProfile,
    WorkerProfile,
    UserData,
)
from apps.authorization.services.secure import make_activation_code
from apps.authorization.services.company_service import CompanyService
from apps.authorization.services.user_service import UserService
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
