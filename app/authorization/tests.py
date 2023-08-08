import logging

import requests
from django.core.exceptions import ObjectDoesNotExist
from django.test import Client, TestCase

from app.authorization.models import UserData
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

    def _login(self) -> requests.Response:
        data = {'email': self.email, 'password': self.password}
        headers = {"accept": "application/json"}
        response = self.client.post(self.login_url, data=data, headers=headers)
        return response

    def setUp(self) -> None:
        logger.debug('Создание тестового пользователя')
        UserData.objects.create_user(self.email, self.password)
        self.client = Client()

    def tearDown(self) -> None:
        logger.info('tearDown')
        try:
            user: UserData = UserData.objects.get(email=self.email)
        except ObjectDoesNotExist as e:
            logger.info('Пользователь %s не найден', self.email)
        else:
            logger.info('Пользователь %s найден, удаляем', self.email)
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
        # new_refresh_token = response.cookies.get(self.refresh_token_name)

        self.assertNotEqual(access_token, new_access_token)
        # self.assertNotEqual(refresh_token, new_refresh_token)

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

    # def test_user_delete(self):
    #     pass
    #
    # def test_visit_test_view(self):
    #     pass
    #
    # def test_register_new_user(self):
    #     pass
    #

