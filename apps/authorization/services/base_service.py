import logging

from django.conf import settings

from apps.authorization.models import (
    CompanyProfile,
    TenantProfile,
    WorkerProfile,
)


logger = logging.getLogger(__name__)


class BaseService:
    @staticmethod
    def get_profile_model(user_type: str):
        """Возвращает профиль юзера"""
        match user_type:
            case settings.ORG:
                profile_model = CompanyProfile
            case settings.WORKER:
                profile_model = WorkerProfile
            case settings.TENANT:
                profile_model = TenantProfile
            case _:
                msg = f'Передан не верный тип профиля пользователя: {user_type}'
                logger.error(msg)
                raise AttributeError(msg)

        return profile_model
