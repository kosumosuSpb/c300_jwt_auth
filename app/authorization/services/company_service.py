from app.authorization.services.base_service import BaseService
from app.authorization.models import (
    CompanyProfile,
    Department,
    UserData
)


class CompanyService(BaseService):
    def __init__(
            self,
            company: CompanyProfile,
            department: Department | None = None
    ):
        self.company = company
        self.department = department

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
        return department
