import logging

from app.authorization.models import UserData
from app.authorization.tests.base_testcase import BaseTestCase
from app.authorization.services.secure import make_activation_code
from config.settings import ACTIVATION


logger = logging.getLogger(__name__)


class TestAccountViews(BaseTestCase):
    def test_registration(self):
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
        expected_code = 201
        jsn = response.json()

        self.assertEqual(response.status_code, expected_code)
        self.assertIn('email', jsn)
        self.assertIn('profile', jsn)
        self.assertNotIn('password', jsn)

        user: UserData = UserData.objects.get(email=self.email_worker)

        if ACTIVATION:
            self.assertFalse(user.is_active)
            self.assertTrue(bool(user.activation_code))

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
