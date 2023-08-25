from django.db import models

from app.authorization.models.user_data import UserData
from app.authorization.models.base_profiles import HumanBaseProfile
from app.authorization.models.company_profile import Department


class WorkerProfile(HumanBaseProfile):
    """
    Профиль пользователя-сотрудника

    Обязательные поля:
        - user - пользователь (аккаунт)
        - position - должность
        - department - отдел
    """
    user = models.OneToOneField(
        UserData,
        on_delete=models.PROTECT,
        related_name='worker_profile'
    )
    position = models.CharField(max_length=75, verbose_name='Должность', null=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        related_name='workers',
        verbose_name='Отдел в компании, в которой работает сотрудник'
    )

    @property
    def company(self):
        """Возвращает компанию, в которой работает сотрудник или None"""
        company = None
        has_department = hasattr(self, 'department')
        has_company = has_department and hasattr(self.department, 'company')

        if has_company:
            company = self.department.company

        return company

    def __repr__(self):
        return f'[worker:{self.pk}:{self.first_name} {self.last_name[:1]}.]'

    def __str__(self):
        return f'[worker:{self.pk}:{self.first_name} {self.last_name[:1]}.]'
