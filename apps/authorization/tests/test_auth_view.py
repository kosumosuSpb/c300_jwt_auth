import datetime as dt
import logging
import sys
from http.cookies import Morsel

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query import QuerySet
from django.test import tag
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authorization.tasks import delete_expired_tokens_from_db
from apps.authorization.tests.base_testcase import BaseTestCase


logger = logging.getLogger(__name__)


class TestAuthViews(BaseTestCase):
    """Тесты авторизации: вход, выход, обновление токена, верификация токена"""

    def test_login(self):
        logger.debug('test_login')

        response = self._login()

        expected_data = {"action": "LOGIN", "status": "OK"}

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(expected_data, response.json())

        logger.debug('cookies: %s', dict(response.cookies))
        self.assertIn(self.access_token_name, response.cookies)
        self.assertIn(self.refresh_token_name, response.cookies)
        self.assertIn(self.csrf_token_name, response.cookies)

    def test_logout(self):
        """Тест выхода пользователя"""
        logger.debug('test_logout')
        response = self._login()
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        refresh_token: Morsel = response.cookies.get(self.refresh_token_name)
        refresh_token: str | None = self._get_value_from_morsel_cookie(refresh_token)
        logger.debug('test_logout | refresh_token: %s', refresh_token)

        refresh_token_object = RefreshToken(refresh_token)  # RefreshToken по факту принимает str

        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # logger.debug('response.cookies: %s', response.cookies)
        # logger.debug('response.headers: %s', response.headers)

        self.assertIn(self.access_token_name, response.cookies)

        access_token_from_cookies = str(response.cookies.get(self.access_token_name))
        expected_empty_access_token = f'{self.access_token_name}=""'
        self.assertIn(expected_empty_access_token, access_token_from_cookies)

        # проверяем, добавился ли рефреш в блеклист
        with self.assertRaises(TokenError):
            refresh_token_object.check_blacklist()

        # если проверять создаётся ли объект BlacklistedToken в БД,
        # то почему-то при запуске теста отдельно -- он создаётся,
        # а при запуске потока тестов -- нет.
        # Но по факту такой проверки -- всё ок

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

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

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

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # TOKEN TESTS

    def test_refresh_token(self):
        """Тест обновления access токена по refresh токену"""
        logger.debug('test_refresh_token')
        response: Response = self._login()

        old_tokens = self._get_tokens_from_response_cookies(response)
        access_token: str | None = old_tokens.get(self.access_token_name)
        refresh_token: str | None = old_tokens.get(self.refresh_token_name)

        response = self.client.post(self.refresh_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_tokens: dict = self._get_tokens_from_response_cookies(response)

        logger.debug('test_refresh_token | new_tokens: %s', new_tokens)

        new_access_token: str | None = new_tokens.get(self.access_token_name)
        self.assertIsNotNone(new_access_token)
        self.assertNotEqual(access_token, new_access_token)

        if settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS'):
            logger.debug('ROTATE_REFRESH_TOKENS is True, check refresh token')
            new_refresh_token = new_tokens.get(self.refresh_token_name)
            self.assertIsNotNone(new_refresh_token)
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
        refresh_token_object = RefreshToken(refresh_token)

        self.client.post(self.refresh_url)

        with self.assertRaises(TokenError, msg='Рефреш токена нет в блоклисте!'):
            refresh_token_object.check_blacklist()
