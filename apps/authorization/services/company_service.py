import logging

from apps.authorization.services.base_service import BaseService
from apps.authorization.models import (
    CompanyProfile,
    Department,
    UserData,
    WorkerProfile
)


logger = logging.getLogger(__name__)


class CompanyService(BaseService):
    def __init__(
            self,
            company: CompanyProfile | int,
    ):
        self.company = self.get_company(company)

    @staticmethod
    def get_company(company_or_id: int | CompanyProfile) -> CompanyProfile:
        """Возвращает объект CompanyProfile"""
        if isinstance(company_or_id, CompanyProfile):
            company = company_or_id
        else:
            company: CompanyProfile = CompanyProfile.objects.get(company_or_id)

        return company

    @staticmethod
    def create_company(
            user: UserData,
            name: str,
            address: str | None = None,
            bank_details: dict | None = None
    ) -> CompanyProfile:
        """Создание профиля компании"""
        company_profile = CompanyProfile.objects.create(
            name=name,
            user=user,
            address=address,
            bank_details=bank_details
        )
        return company_profile

    @staticmethod
    def create_department(
            company: CompanyProfile,
            name: str,
    ) -> Department:
        """Создание профиля отдела"""
        department = Department.objects.create(company=company, name=name)
        logger.debug('Создан отдел: %s', department)

        return department

    @staticmethod
    def link_worker_to_department(
            worker: UserData | WorkerProfile,
            department: Department
    ) -> UserData:
        """Связывание сотрудника с отделом"""
        if isinstance(worker, UserData):
            assert hasattr(worker, 'worker_profile'), 'Пользователь не связан с профилем сотрудника!'
            worker_profile = worker.worker_profile
        elif isinstance(worker, WorkerProfile):
            worker_profile = worker
        else:
            msg = 'Не правильный тип атрибута: должен быть UserData или WorkerProfile!'
            logger.error(msg)
            raise AttributeError(msg)

        worker_profile.department = department

        return worker_profile
