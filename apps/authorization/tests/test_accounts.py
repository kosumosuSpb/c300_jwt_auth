import datetime as dt
import sys
import logging

import requests
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models.query import QuerySet
from django.test import tag, override_settings
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework import status

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
from apps.authorization.tasks import delete_expired_tokens_from_db


logger = logging.getLogger(__name__)


class TestAccount(BaseTestCase):
    """Тесты аккаунта: вход, выход, обновление токена, удаление пользователя"""
    def test_login(self):
        logger.debug('test_login')

        response = self._login()

        expected_data = {"action": "LOGIN", "status": "OK"}
        self.assertEqual(200, response.status_code)
        self.assertEqual(expected_data, response.json())

        logger.debug('cookies: %s', dict(response.cookies))
        self.assertIn(self.access_token_name, response.cookies)
        self.assertIn(self.refresh_token_name, response.cookies)
        self.assertIn(self.csrf_token_name, response.cookies)  # опционально, для теста не обязательно

    def test_logout(self):
        """Тест выхода пользователя"""
        logger.debug('test_logout')
        response = self._login()
        self.assertEquals(200, response.status_code)

        access_token = response.cookies.get(self.access_token_name)
        csrf_token = response.cookies.get(self.csrf_token_name)

        cookies = {
            self.access_token_name: access_token,
            # self.csrf_token_name: csrf_token
        }
        headers = {
            self.csrf_headers_name: csrf_token
        }
        response = self.client.post(self.logout_url, cookies=cookies, headers=headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # logger.debug('response.cookies: %s', response.cookies)
        # logger.debug('response.headers: %s', response.headers)

        self.assertIn(self.access_token_name, response.cookies)

        cookies_access_token = str(response.cookies.get(self.access_token_name))
        expected_empty_access_token = f'{self.access_token_name}=""'
        self.assertIn(expected_empty_access_token, cookies_access_token)

    def test_login_invalid_email(self):
        logger.debug('test_invalid_email')
        data = {'email': 'some_invalid@email.com', 'password': self.password}
        headers = {"accept": "application/json"}
        response = self.client.post(
            self.login_url,
            data=data,
            headers=headers,
            content_type="application/json"
        )

        self.assertEqual(401, response.status_code)

    def test_login_invalid_password(self):
        logger.debug('test_invalid_password')
        data = {'email': self.email, 'password': self.password + 'h'}
        headers = {"accept": "application/json"}
        response = self.client.post(
            self.login_url,
            data=data,
            headers=headers,
            content_type="application/json"
        )

        self.assertEqual(401, response.status_code)

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

    # TOKENS TESTS

    def test_refresh_token(self):
        logger.debug('test_refresh_token')
        response: requests.Response = self._login()
        access_token = response.cookies.get(self.access_token_name)
        refresh_token = response.cookies.get(self.refresh_token_name)

        cookies = {self.refresh_token_name: refresh_token}
        response = self.client.post(self.refresh_url, cookies=cookies)

        self.assertEqual(response.status_code, 200)
        new_access_token = response.cookies.get(self.access_token_name)
        self.assertTrue(bool(new_access_token))
        self.assertNotEqual(access_token, new_access_token)

        if settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS'):
            logger.debug('ROTATE_REFRESH_TOKENS is True, check refresh token')
            new_refresh_token = response.cookies.get(self.refresh_token_name)
            self.assertTrue(bool(new_refresh_token))
            self.assertNotEqual(refresh_token, new_refresh_token)

    def test_csrf_token_in_cookies(self):
        logger.debug('test_csrf_token_in_cookies_and_headers')
        response = self._login()

        csrf_token_cookies = response.cookies.get(self.csrf_token_name)
        self.assertIsNotNone(csrf_token_cookies)

    # BLACKLIST TESTS

    def test_task_delete_expired_tokens(self):
        """Тест на удаление просроченных токенов"""
        response = self._login()
        tokens = self._get_tokens_from_response_cookies(response)
        refresh_token = tokens.get(self.refresh_token_name)

        outstanding_token = OutstandingToken.objects.get(token=refresh_token)
        self.assertTrue(bool(outstanding_token))
        logger.debug('OUTSTANDING_TOKEN: %s', outstanding_token)

        now = dt.datetime.now()
        outstanding_token.expires_at = now
        outstanding_token.save()

        delete_expired_tokens_from_db.run()  # celery task

        with self.assertRaises(ObjectDoesNotExist):
            outstanding_token = OutstandingToken.objects.get(token=refresh_token)
            # logger.debug('OUTSTANDING_TOKEN after delete: %s', outstanding_token)

    @tag('blacklist')
    def test_add_refresh_to_outstanding_db(self):
        """Тест на добавление рефреш токена в БД"""
        logger.debug('test_add_refresh_to_outstanding_db')

        start_blacklist = 'blacklist' in str(sys.argv)
        if not start_blacklist:
            skip_msg = 'Тест test_add_refresh_to_outstanding_db пропущен из за условия'
            logger.debug(skip_msg)
            self.skipTest(skip_msg)

        response = self._login()

        tokens = self._get_tokens_from_response_cookies(response)
        refresh_token = tokens.get(self.refresh_token_name)
        # logger.debug('refresh_token: %s', refresh_token)
        self.assertTrue(bool(refresh_token), 'Рефреш токена нет в ответе от логина!')

        queryset: QuerySet = OutstandingToken.objects.filter(token=refresh_token)
        self.assertTrue(queryset.exists(), 'Рефреш токена в БД нет!')
        self.assertEqual(1, queryset.count(), 'Нашлось больше одного объекта с этим токеном!')

    @tag('blacklist')
    def test_add_refresh_to_blacklist_db(self):
        """Тест на добавление рефреш токена в блеклист после рефреша"""
        logger.debug('test_add_refresh_to_blacklist_db')

        start_blacklist = 'blacklist' in str(sys.argv)
        if not start_blacklist:
            skip_msg = 'Тест test_add_refresh_to_blacklist_db пропущен из за условия'
            logger.debug(skip_msg)
            self.skipTest(skip_msg)

        response = self._login()
        tokens = self._get_tokens_from_response_cookies(response)
        refresh_token = tokens.get(self.refresh_token_name)

        cookies = {self.refresh_token_name: refresh_token}
        response = self.client.delete(self.refresh_url, cookies=cookies)

        outstanding_qs = OutstandingToken.objects.filter(token=refresh_token)
        self.assertTrue(outstanding_qs.exists(), 'Рефреш токена в БД нет!')
        self.assertEqual(1, outstanding_qs.count(), 'Нашлось больше одного объекта с этим токеном!')
        outstanding_id = outstanding_qs.get()

        blacklist_qs = BlacklistedToken.objects.filter(token_id=outstanding_id)

        self.assertTrue(blacklist_qs.exists(), 'Рефреш токена нет в блоклисте!')
        self.assertEqual(1, blacklist_qs.count(), 'Нашлось больше одного объекта токена с этим id!')
