import logging
from unittest.mock import patch

from django.core.exceptions import ObjectDoesNotExist
from django.test import override_settings
from rest_framework.response import Response
from rest_framework import status

from apps.authorization.models import UserData
from apps.authorization.tests.base_testcase import BaseTestCase
from apps.authorization.services.secure import make_activation_code
from apps.authorization.tasks import send_activation_mail


logger = logging.getLogger(__name__)


class TestAccountViews(BaseTestCase):
    def _create_worker_over_view(self) -> Response:
        """Создание воркера через представление"""
        data = {
            'email': self.email_worker,
            'password': self.password_worker,
            'profile': self.worker_profile_male
        }

        logger.debug('test_registration | data: %s', data)

        response = self.client.post(
            self.reg_url,
            data=data,
            content_type="application/json"
        )
        return response

    @patch.object(send_activation_mail, 'delay')
    @override_settings(ACTIVATION=True)
    def test_activation_celery_task_called(self, *args, **kwargs):
        logger.debug('STARTED test_activation_celery_task_called')

        self._create_worker_over_view()
        send_activation_mail.delay.assert_called()

    @patch.object(send_activation_mail, 'delay')
    @override_settings(ACTIVATION=True)
    def test_registration_with_activation(self, *args, **kwargs):
        response = self._create_worker_over_view()

        expected_code = 201
        jsn = response.json()

        self.assertEqual(response.status_code, expected_code)
        self.assertIn('email', jsn)
        self.assertIn('profile', jsn)
        self.assertNotIn('password', jsn)

        user: UserData = UserData.objects.get(email=self.email_worker)

        self.assertFalse(user.is_active)
        self.assertTrue(bool(user.activation_code))

    @patch.object(send_activation_mail, 'delay')
    @override_settings(ACTIVATION=False)
    def test_registration_without_activation(self, *args, **kwargs):
        response = self._create_worker_over_view()

        expected_code = 201
        jsn = response.json()

        self.assertEqual(response.status_code, expected_code)
        self.assertIn('email', jsn)
        self.assertIn('profile', jsn)
        self.assertNotIn('password', jsn)

        user: UserData = UserData.objects.get(email=self.email_worker)

        self.assertTrue(user.is_active)
        self.assertFalse(bool(user.activation_code))

    def test_activation_view(self):
        """Тест активации через представление активации"""
        user: UserData = UserData.objects.get(email=self.email)
        user.is_active = False
        activation_code = make_activation_code()
        user.activation_code = activation_code
        user.save()

        params = {
            'user_id': user.pk,
            'activation_code': activation_code
        }

        response = self.client.get(self.activation_url, params)

        expected_code = 202
        self.assertEqual(response.status_code, expected_code)

        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertIsNone(user.activation_code)

    def test_delete_user(self):
        """Тест удаления юзера"""
        logger.debug('test_delete_user')
        user = UserData.objects.get(email=self.email)
        user.is_superuser = True
        user.save()

        user_worker = self._create_worker()

        self._login()

        response = self.client.delete(self.delete_user_url + str(user_worker.pk) + '/')

        logger.debug('test_delete_user | response.content: %s', response.content)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(ObjectDoesNotExist):
            UserData.objects.get(pk=user_worker.pk)

    def test_mark_as_deleted_user(self):
        """Тест удаления юзера"""
        logger.debug('test_mark_as_deleted_user')
        user = UserData.objects.get(email=self.email)
        user.is_superuser = True
        user.save()

        user_worker = self._create_worker()

        self._login()

        response = self.client.patch(self.delete_user_url + str(user_worker.pk) + '/')

        logger.debug('test_mark_as_deleted_user | response.content: %s', response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user_worker.refresh_from_db()
        self.assertTrue(user_worker.is_deleted)
        self.assertFalse(user_worker.is_active)
