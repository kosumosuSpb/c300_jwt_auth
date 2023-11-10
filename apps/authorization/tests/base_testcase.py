import logging
from http.cookies import Morsel

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.test import Client
from rest_framework.response import Response
from rest_framework.test import APITestCase

from apps.authorization.models.user_data import UserData
from apps.authorization.models.company_profile import CompanyProfile, Department
from apps.authorization.services.user_service import UserService
from apps.authorization.services.permissions import PermissionService


logger = logging.getLogger(__name__)


class BaseTestCase(APITestCase):
    """Базовый класс для тестирования"""
    # fixtures = ['auth.json']

    @classmethod
    def setUpTestData(cls):
        # ENDPOINTS
        base_api_url = '/' + settings.API_BASE_URL
        cls.login_url = base_api_url + 'auth/login/'
        cls.refresh_url = base_api_url + 'auth/refresh/'
        cls.logout_url = base_api_url + 'auth/logout/'
        cls.delete_user_url = base_api_url + 'account/delete/'
        cls.show_user_ulr = base_api_url + 'account/profile/'
        cls.test_url = base_api_url + 'account/test/'
        cls.activation_url = base_api_url + 'account/activate/'
        cls.reg_url = base_api_url + 'account/register/'
        cls.perms_url = base_api_url + 'permissions/'
        cls.perms_one_url = base_api_url + 'permissions/create_one/'
        cls.perms_grant_url = base_api_url + 'permissions/grant/'

        # ACC VARIABLES
        cls.email = 'base@email.one'
        cls.password = 'somePassWord1'

        cls.email_org1 = 'company1@email.one'
        cls.password_org1 = 'somePassWord_company1'
        cls.org_profile1 = {
            'type': 'company',
            'name': 'Company1'
        }
        cls.email_org1 = 'company2@email.one'
        cls.password_org1 = 'somePassWord_company2'
        cls.org_profile2 = {
            'type': 'company',
            'name': 'Company2'
        }

        cls.department_name1 = 'Department1'
        cls.department_name2 = 'Department2'

        # offset = datetime.timedelta(hours=3)
        # tz = datetime.timezone(offset, name='msk')
        cls.datetime_str = "2000-08-25T12:00:00+03:00"

        cls.email_worker = 'worker1@email.one'
        cls.password_worker = 'somePassWord_worker1'
        cls.worker_profile_male = {
            'type': 'worker',
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'birth_date': cls.datetime_str,
            'sex': 'male'
        }
        cls.email_worker = 'worker2@email.one'
        cls.password_worker = 'somePassWord_worker2'
        cls.worker_profile_female = {
            'type': 'worker',
            'first_name': 'Мария',
            'last_name': 'Мариева',
            'birth_date': cls.datetime_str,
            'sex': 'female'
        }

        cls.email_tenant = 'tenant@email.one'
        cls.password_tenant = 'somePassWord_tenant1'
        cls.tenant_profile = {
            'type': 'tenant',
            'first_name': 'Пётр',
            'last_name': 'Петров',
            'birth_date': cls.datetime_str,
            'sex': 'male'
        }

        # TOKEN VARIABLES
        cls.access_token_name = settings.SIMPLE_JWT['AUTH_COOKIE']
        cls.refresh_token_name = settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH']
        cls.csrf_token_name = settings.CSRF_COOKIE_NAME
        cls.csrf_headers_name = settings.CSRF_HEADERS_NAME

        # PERMISSION VARS
        cls.permission_name = 'some_cool_action'

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
            logger.debug('Пользователь %s не найден (%s)', self.email, e)
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
        response = client.post(
            self.login_url,
            data=data,
            headers=headers,
            content_type="application/json"
        )
        return response

    @staticmethod
    def _get_value_from_morsel_cookie(cookie: Morsel) -> str | None:
        """
        Извлечение значения из типа http.cookies.Morsel,
        который используется в тестовом клиенте

        Args:
            cookie: http.cookies.Morsel

        Returns: str
        """
        if cookie is None:
            logger.warning('_get_value_from_morsel_cookie | пришёл None! Возвращаю None...')
            return None

        assert isinstance(cookie, Morsel), \
            f'Пришёл не верный класс, должен быть Morsel, а на самом деле - {type(cookie)}'
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
            profile: dict | None = None
    ) -> UserData:
        """Создание пользователя с профилем компании"""
        user_company = UserService.create_user(
            email=email or self.email_org1,
            password=password or self.password_org1,
            profile=profile or self.org_profile1
        )
        return user_company

    def _create_department(self, company: CompanyProfile) -> Department:
        """Создание отдела"""
        dep = Department.objects.create(company=company, name=self.department_name1)
        self.assertIsInstance(dep, Department)
        return dep

    # WORKER
    def _create_worker(
            self,
            email: str | None = None,
            password: str | None = None,
            profile: dict | None = None,
            sex='male'
    ) -> UserData:
        """Создание пользователя с профилем сотрудника/работника"""
        if sex == 'male':
            user_worker = UserService.create_user(
                email=email or self.email_worker,
                password=password or self.password_worker,
                profile=profile or self.worker_profile_male
            )
        elif sex == 'female':
            user_worker = UserService.create_user(
                email=email or self.email_worker,
                password=password or self.password_worker,
                profile=profile or self.worker_profile_female
            )
        else:
            raise ValueError('Указан не верный пол, доступно только два: male и female')

        return user_worker

    # TENANT
    def _create_tenant(
            self,
            email: str | None = None,
            password: str | None = None,
            profile: dict | None = None,
    ) -> UserData:
        """Создание пользователя с профилем жителя"""
        user_tenant = UserService.create_user(
            email=email or self.email_tenant,
            password=password or self.password_tenant,
            profile=profile or self.tenant_profile
        )
        return user_tenant

    def _create_company_and_worker(self, as_tuple=False) -> dict[str, UserData | Department]:
        """Создаёт компанию, отдел и сотрудника"""
        company_user = self._create_company()
        department = self._create_department(company_user.profile)
        worker_user = self._create_worker()
        department.workers.add(worker_user.worker_profile)

        if as_tuple:
            company = (company_user, department, worker_user)
        else:
            company = {
                'company_user': company_user,
                'department': department,
                'worker_user': worker_user
            }

        return company

    # PERMISSIONS

    def _create_permission(self, name: str | None = None) -> list:
        """Создание CRUD-прав (4 штук) через PermissionService. Возвращает list[PermissionModel]"""
        name = name or self.permission_name
        logger.debug('Создание права %s через сервис прав', name)
        perms_models = PermissionService.create_permissions(name)
        return perms_models
