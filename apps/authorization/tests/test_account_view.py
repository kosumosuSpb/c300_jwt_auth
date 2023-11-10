import logging
from unittest.mock import patch

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.test import override_settings
from rest_framework import status
from rest_framework.response import Response

from apps.authorization.models import UserData
from apps.authorization.tests.base_testcase import BaseTestCase
from apps.authorization.services.secure import make_activation_code
from apps.authorization.tasks import send_activation_mail


logger = logging.getLogger(__name__)


class TestAccountViews(BaseTestCase):
    """Тесты аккаунта: регистрация, активация, удаление пользователя"""

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

        jsn = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
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

        jsn: dict = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
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

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertIsNone(user.activation_code)

    def test_show_user_worker(self):
        """Краткий тест отображения информации о сотруднике"""
        logger.debug('test_show_user')
        user_worker = self._create_worker()
        self._login()

        response: Response = self.client.get(self.show_user_ulr + str(user_worker.pk) + '/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user_data: dict = response.json()
        self.assertIsNotNone(user_data)
        self.assertIsInstance(user_data, dict)
        self.assertIn('email', user_data)
        self.assertIn('profile', user_data)
        user_fields = (
            'is_superuser', 'is_staff', 'is_active', 'date_joined', 'phones',
            'is_admin', 'number', 'avatar', 'inn', 'get_access_date', 'is_deleted'
        )
        all_contains = all([field in user_data for field in user_fields])
        self.assertTrue(all_contains)

        profile = user_data.get('profile')
        self.assertIsNotNone(profile)
        self.assertIsInstance(profile, dict)

        profile_type = profile.get('type')
        self.assertIsNotNone(profile_type)
        self.assertEqual(profile_type, settings.WORKER)

        fields = ('type', 'first_name', 'last_name', 'birth_date', 'sex')
        all_contains = all([field in profile for field in fields])
        self.assertTrue(all_contains)

    def test_show_user_tenant(self):
        """Краткий тест отображения информации о жителе"""
        logger.debug('test_show_user')
        user_tenant = self._create_tenant()
        self._login()

        response: Response = self.client.get(self.show_user_ulr + str(user_tenant.pk) + '/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user_data: dict = response.json()
        self.assertIsNotNone(user_data)
        self.assertIsInstance(user_data, dict)
        self.assertIn('email', user_data)
        self.assertIn('profile', user_data)
        user_fields = (
            'is_superuser', 'is_staff', 'is_active', 'date_joined', 'phones',
            'is_admin', 'number', 'avatar', 'inn', 'get_access_date', 'is_deleted'
        )
        all_contains = all([field in user_data for field in user_fields])
        self.assertTrue(all_contains)

        profile = user_data.get('profile')
        self.assertIsNotNone(profile)
        self.assertIsInstance(profile, dict)

        profile_type = profile.get('type')
        self.assertIsNotNone(profile_type)
        self.assertEqual(profile_type, settings.TENANT)

        fields = ('type', 'first_name', 'last_name', 'birth_date', 'sex')
        all_contains = all([field in profile for field in fields])
        self.assertTrue(all_contains)

    def test_show_user_company(self):
        """Краткий тест отображения информации о жителе"""
        logger.debug('test_show_user')
        user_company = self._create_company()
        self._login()

        response: Response = self.client.get(self.show_user_ulr + str(user_company.pk) + '/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user_data: dict = response.json()
        self.assertIsNotNone(user_data)
        self.assertIsInstance(user_data, dict)
        self.assertIn('email', user_data)
        self.assertIn('profile', user_data)
        user_fields = (
            'is_superuser', 'is_staff', 'is_active', 'date_joined', 'phones',
            'is_admin', 'number', 'avatar', 'inn', 'get_access_date', 'is_deleted'
        )
        all_contains = all([field in user_data for field in user_fields])
        self.assertTrue(all_contains)

        profile = user_data.get('profile')
        self.assertIsNotNone(profile)
        self.assertIsInstance(profile, dict)

        profile_type = profile.get('type')
        self.assertIsNotNone(profile_type)
        self.assertEqual(profile_type, settings.ORG)

        profile_fields = ('type', 'name', 'bank_details', 'address')
        all_contains = all([field in profile for field in profile_fields])
        self.assertTrue(all_contains)

    def test_worker_profile_edit(self):
        """Тест редактирования профиля пользователя-сотрудника"""
        new_data = {
            'profile': {
                "type": "tenant",
                "first_name": "Мария",
                "last_name": "Иванова",
                "birth_date": "2001-10-05T12:00:00+03:00",
                "sex": "female"
            }
        }
        user_worker = self._create_worker(sex='female')
        old_last_name: str = user_worker.profile.last_name
        new_last_name: str = new_data['profile']['last_name']

        self._login()

        response = self.client.put(
            self.show_user_ulr + str(user_worker.pk) + '/',
            data=new_data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user_worker.refresh_from_db()

        self.assertNotEqual(user_worker.profile.last_name, old_last_name)
        self.assertEqual(user_worker.profile.last_name, new_last_name)

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
        """Тест пометки юзера, как удалённого"""
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
