import logging

from app.authorization.tests.base_testcase import BaseTestCase


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

    # def test_activation(self):
    #     """Тест активации"""
