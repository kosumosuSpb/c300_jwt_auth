import logging

from rest_framework import serializers

from app.authorization.models import (
    UserData,
    CompanyProfile,
    WorkerProfile,
    TenantProfile,
    Department,
)
from app.authorization.services.user_service import UserService
from app.authorization.services.company_service import CompanyService
from config.settings import ORG, TENANT, WORKER


logger = logging.getLogger(__name__)


class CompanyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfile
        exclude = ['user']


class WorkerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerProfile
        exclude = ['user']


class TenantProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantProfile
        exclude = ['user']


class UserSerializer(serializers.ModelSerializer):
    profile = serializers.JSONField()

    class Meta:
        model = UserData
        exclude = ['user_permissions', 'groups']
        extra_kwargs = {
            'password': {'write_only': True},
            'activation_code': {'write_only': True},
        }

    def validate_profile(self, profile: dict):
        """Валидация поля профиля"""
        logger.debug('validate_profile | Profile data: %s', profile)

        user_type = profile.get('type')
        if user_type == ORG:
            profile_serializer = CompanyProfileSerializer(data=profile)
        elif user_type == WORKER:
            profile_serializer = WorkerProfileSerializer(data=profile)
        elif user_type == TENANT:
            profile_serializer = TenantProfileSerializer(data=profile)
        else:
            msg = 'Передан не верный тип профиля пользователя (в "profiles")!'
            logger.error(msg)
            raise serializers.ValidationError(detail=msg)

        profile_serializer.is_valid(raise_exception=True)

        logger.debug('validate_profile | Profile validated data: %s',
                     profile_serializer.validated_data)

        return profile


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'
