import sys
import logging
import datetime
from http.cookies import Morsel

import requests
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models.query import QuerySet
from django.test import Client, tag
from rest_framework.response import Response
from rest_framework.test import APITestCase
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from app.authorization.models import *
# from app.authorization.models.user_data import UserData
# from app.authorization.models.company_profile import CompanyProfile, Department
from app.authorization.services.user_service import UserService
from app.authorization.services.company_service import CompanyService
from config.settings import SIMPLE_JWT, CSRF_COOKIE_NAME, CSRF_HEADERS_NAME


logger = logging.getLogger(__name__)


class BaseTestCase(APITestCase):
    """Базовый класс для тестирования"""
    # fixtures = ['auth.json']

    @classmethod
    def setUpTestData(cls):
        # ENDPOINTS
        cls.login_url = '/api/v1/login/'
        cls.refresh_url = '/api/v1/login/refresh/'
        cls.logout_url = '/api/v1/logout/'
        cls.test_url = '/api/v1/test/'
        # ACC VARIABLES
        cls.email = 'base@email.one'
        cls.password = 'somePassWord1'

        cls.email_org1 = 'company1@email.one'
        cls.email_org2 = 'company2@email.one'
        cls.password_org1 = 'somePassWord_company1'
        cls.password_org2 = 'somePassWord_company2'
        cls.company_name1 = 'Company1'
        cls.company_name2 = 'Company2'
        cls.department_name1 = 'Department1'
        cls.department_name2 = 'Department2'

        cls.first_name = 'Иван'
        cls.last_name = 'Иванов'

        offset = datetime.timedelta(hours=3)
        tz = datetime.timezone(offset, name='msk')
        cls.birth_date = datetime.datetime.now(tz=tz)
        cls.sex = 'male'

        cls.email_worker = 'worker@email.one'
        cls.password_worker = 'somePassWord_worker1'

        cls.email_tenant = 'tenant@email.one'
        cls.password_tenant = 'somePassWord_tenant1'
        # TOKEN VARIABLES
        cls.access_token_name = SIMPLE_JWT['AUTH_COOKIE']
        cls.refresh_token_name = SIMPLE_JWT['AUTH_COOKIE_REFRESH']
        cls.csrf_token_name = CSRF_COOKIE_NAME
        cls.csrf_headers_name = CSRF_HEADERS_NAME

    def setUp(self) -> None:
        logger.debug('setUp | Создание объекта UserData')
        UserData.objects.create_user(
            self.email,
            self.password,
        )
        self.client = Client()

    def tearDown(self) -> None:
        logger.debug('tearDown | Удаление тестового пользователя UserData')
        try:
            user: UserData = UserData.objects.get(email=self.email)
        except ObjectDoesNotExist as e:
            logger.debug('Пользователь %s не найден', self.email)
        else:
            logger.debug('Пользователь %s найден, удаляем', self.email)
            user.delete()

    def _login(
            self,
            email: str | None = None,
            password: str | None = None,
            client: Client | None = None
    ) -> Response:
        """
        Делает логин базового пользователя UserData,
        либо пользователя, логин и пароль которого прописан

        :param client: Тестовый клиент для теста эндпоинта.
            Нужен для того, чтобы можно было создать,
            например Client(enforce_csrf_checks=True) и передать сюда
        :return: Response
        """
        if email or password:
            assert email and password, 'Если указан email, то должен быть указан и password!'

        email = email or self.email
        password = password or self.password

        data = {'email': email, 'password': password}
        headers = {"accept": "application/json"}
        client = client or self.client
        response = client.post(self.login_url, data=data, headers=headers)
        return response

    @staticmethod
    def _get_value_from_morsel_cookie(cookie: Morsel):
        """
        Извлечение значения из типа http.cookies.Morsel,
        который используется в тестовом клиенте

        Args:
            cookie: http.cookies.Morsel

        Returns: None
        """
        assert isinstance(cookie, Morsel), 'Пришёл не верный класс, должен быть Morsel'
        assert hasattr(cookie, '_value'), 'У объекта нет поля _value!'
        return cookie._value

    def _get_tokens_from_response_cookies(self, response: Response, as_tuple=False) -> dict | tuple:
        """
        Вытаскивает токены из Response

        :param response: Response object
        :param as_tuple: Флаг для возможности вывести кортежем
        :return: dict {access_token: access_token, ...} или кортеж (access, refresh, csrf)
        """
        access_token = response.cookies.get(self.access_token_name)
        access_token = self._get_value_from_morsel_cookie(access_token)

        refresh_token = response.cookies.get(self.refresh_token_name)
        refresh_token = self._get_value_from_morsel_cookie(refresh_token)

        csrf_token = response.cookies.get(self.csrf_token_name)
        csrf_token = self._get_value_from_morsel_cookie(csrf_token)

        if as_tuple:
            tokens = (access_token, refresh_token, csrf_token)
        else:
            tokens = {
                self.access_token_name: access_token,
                self.refresh_token_name: refresh_token,
                self.csrf_token_name: csrf_token
            }
        return tokens

    # CREATE USERS WITH PROFILES
    # COMPANY
    def _create_company(
            self,
            email: str | None = None,
            password: str | None = None,
            org_name: str | None = None
    ) -> UserData:
        user_company = UserService.create_user(
            UserData.ORG,
            email=email or self.email_org1,
            password=password or self.password_org1,
            org_name=org_name or self.company_name1
        )
        return user_company

    def _create_department(self, company: CompanyProfile) -> Department:
        dep = Department.objects.create(company=company, name=self.department_name1)
        self.assertIsInstance(dep, Department)
        return dep

    # WORKER
    def _create_worker(
            self,
            email: str | None = None,
            password: str | None = None,
            *,
            first_name: str | None = None,
            last_name: str | None = None,
            birth_date: str | None = None,
            sex: str | None = None
    ) -> UserData:
        user_worker = UserService.create_user(
            UserData.WORKER,
            email=email or self.email_worker,
            password=password or self.password_worker,
            first_name=first_name or self.first_name,
            last_name=last_name or self.last_name,
            birth_date=birth_date or self.birth_date,
            sex=sex or self.sex
        )
        return user_worker

    # TENANT
    def _create_tenant(
            self,
            email: str | None = None,
            password: str | None = None,
            *,
            first_name: str | None = None,
            last_name: str | None = None,
            birth_date: str | None = None,
            sex: str | None = None
    ) -> UserData:
        user_tenant = UserService.create_user(
            UserData.TENANT,
            email=email or self.email_tenant,
            password=password or self.password_tenant,
            first_name=first_name or self.first_name,
            last_name=last_name or self.last_name,
            birth_date=birth_date or self.birth_date,
            sex=sex or self.sex
        )
        return user_tenant


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

        expected_data = {
            "action": "LOGOUT",
            "status": "OK"
        }
        self.assertEqual(200, response.status_code)
        self.assertEqual(expected_data, response.json())

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
        response = self.client.post(self.login_url, data=data, headers=headers)

        self.assertEqual(401, response.status_code)

    def test_login_invalid_password(self):
        logger.debug('test_invalid_password')
        data = {'email': self.email, 'password': self.password + 'h'}
        headers = {"accept": "application/json"}
        response = self.client.post(self.login_url, data=data, headers=headers)

        self.assertEqual(401, response.status_code)

    def test_create_company(self):
        logger.debug('test_create_company')
        user_company = self._create_company()
        self.assertIsInstance(user_company, UserData)
        self.assertTrue(hasattr(user_company, 'company_profile'))
        self.assertIsInstance(user_company.company_profile, CompanyProfile)

    def test_create_department(self):
        user_company = self._create_company()
        profile: CompanyProfile = user_company.company_profile
        department = self._create_department(profile)
        self.assertIsInstance(department, Department)

    def test_create_worker(self):
        logger.debug('test_create_worker')
        user_worker = self._create_worker()
        self.assertIsInstance(user_worker, UserData)
        self.assertTrue(hasattr(user_worker, 'worker_profile'))
        self.assertIsInstance(user_worker.worker_profile, WorkerProfile)

    def test_link_worker_to_department(self):
        user_worker = self._create_worker()
        user_company = self._create_company()
        dep = self._create_department(user_company.company_profile)
        CompanyService.link_worker_to_department(user_worker.worker_profile, dep)

    def test_create_tenant(self):
        logger.debug('test_create_tenant')
        user_tenant = self._create_tenant()
        self.assertIsInstance(user_tenant, UserData)
        self.assertTrue(hasattr(user_tenant, 'tenant_profile'))
        self.assertIsInstance(user_tenant.tenant_profile, TenantProfile)

    def test_create_already_created_user(self):
        logger.debug('test_register_already_registered_user')
        with self.assertRaises(ValidationError):
            UserService.create_user(UserData.TENANT, self.email, self.password)

    def test_create_user_with_wrong_email(self):
        logger.debug('test_create_user_with_wrong_email')
        with self.assertRaises(ValidationError):
            user_tenant = self._create_tenant(email='aerg')

    # TOKENS TESTS

    def test_refresh_token(self):
        logger.debug('test_refresh_token')
        response: requests.Response = self._login()
        access_token = response.cookies.get(self.access_token_name)
        refresh_token = response.cookies.get(self.refresh_token_name)

        cookies = {self.refresh_token_name: refresh_token}
        response = self.client.post(self.refresh_url, cookies=cookies)
        new_access_token = response.cookies.get(self.access_token_name)
        self.assertNotEqual(access_token, new_access_token)

        if SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS'):
            logger.debug('ROTATE_REFRESH_TOKENS is True, check refresh token')
            new_refresh_token = response.cookies.get(self.refresh_token_name)
            self.assertNotEqual(refresh_token, new_refresh_token)

    def test_csrf_token_in_cookies(self):
        logger.debug('test_csrf_token_in_cookies_and_headers')
        response = self._login()

        csrf_token_cookies = response.cookies.get(self.csrf_token_name)
        self.assertIsNotNone(csrf_token_cookies)

    # BLACKLIST TESTS

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
        response = self.client.post(self.refresh_url, cookies=cookies)

        outstanding_qs = OutstandingToken.objects.filter(token=refresh_token)
        self.assertTrue(outstanding_qs.exists(), 'Рефреш токена в БД нет!')
        self.assertEqual(1, outstanding_qs.count(), 'Нашлось больше одного объекта с этим токеном!')
        outstanding_id = outstanding_qs.get()

        blacklist_qs = BlacklistedToken.objects.filter(token_id=outstanding_id)

        self.assertTrue(blacklist_qs.exists(), 'Рефреш токена нет в блоклисте!')
        self.assertEqual(1, blacklist_qs.count(), 'Нашлось больше одного объекта токена с этим id!')
