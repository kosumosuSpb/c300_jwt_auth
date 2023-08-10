import sys
import logging
from http.cookies import Morsel

import requests
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models.query import QuerySet
from django.test import Client, TestCase, tag
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from app.authorization.models import UserData
from app.authorization.services.user_service import UserService
from config.settings import SIMPLE_JWT, CSRF_COOKIE_NAME, CSRF_HEADERS_NAME


logger = logging.getLogger(__name__)


class TestAccount(TestCase):
    """Тесты аккаунта: вход, выход, обновление токена, удаление пользователя"""
    @classmethod
    def setUpTestData(cls):
        # ENDPOINTS
        cls.login_url = '/api/v1/login/'
        cls.refresh_url = '/api/v1/login/refresh/'
        cls.logout_url = '/api/v1/logout/'
        cls.test_url = '/api/v1/test/'
        # VARIABLES
        cls.email = 'some@email.one'
        cls.password = 'somePassWord1'
        cls.access_token_name = SIMPLE_JWT['AUTH_COOKIE']
        cls.refresh_token_name = SIMPLE_JWT['AUTH_COOKIE_REFRESH']
        cls.csrf_token_name = CSRF_COOKIE_NAME
        cls.csrf_headers_name = CSRF_HEADERS_NAME

    def _login(self, client: Client | None = None) -> Response:
        """
        Делает логин

        :param client: Тестовый клиент для теста эндпоинта.
            Нужен для того, чтобы можно было создать,
            например Client(enforce_csrf_checks=True) и передать сюда
        :return: Response
        """
        data = {'email': self.email, 'password': self.password}
        headers = {"accept": "application/json"}
        client = client or self.client
        response = client.post(self.login_url, data=data, headers=headers)
        return response

    @staticmethod
    def _get_value_from_morsel_cookie(cookie: Morsel):
        """Извлечение значения из типа http.cookies.Morsel"""
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

    def setUp(self) -> None:
        logger.debug('setUp | Создание тестового пользователя')
        UserData.objects.create_user(self.email, self.password)
        self.client = Client()

    def tearDown(self) -> None:
        logger.debug('tearDown | Удаление тестового пользователя')
        try:
            user: UserData = UserData.objects.get(email=self.email)
        except ObjectDoesNotExist as e:
            logger.debug('Пользователь %s не найден', self.email)
        else:
            logger.debug('Пользователь %s найден, удаляем', self.email)
            user.delete()

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

    # def test_login_logout_login(self):
    #     pass

    def test_create_already_created_user(self):
        logger.debug('test_register_already_registered_user')
        with self.assertRaises(ValidationError):
            UserService.create_user(self.email, self.password)

    def test_create_user_with_wrong_email(self):
        logger.debug('test_create_user_with_wrong_email')
        with self.assertRaises(ValidationError):
            UserService.create_user('some_another', 'PassWord_672')

    def test_create_another_user(self):
        logger.debug('test_create_another_user')
        user = UserService.create_user('some_another@mail.ne')
        self.assertIsInstance(user, UserData)

    def test_csrf_token_in_cookies(self):
        logger.debug('test_csrf_token_in_cookies_and_headers')
        response = self._login()

        csrf_token_cookies = response.cookies.get(self.csrf_token_name)
        self.assertIsNotNone(csrf_token_cookies)

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
