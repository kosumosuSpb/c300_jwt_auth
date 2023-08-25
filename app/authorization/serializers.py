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

    def create(self, validated_data):
        logger.debug('UserSerializer | data: %s', self.data)
        logger.debug('UserSerializer | Validated data: %s', validated_data)

        email = validated_data.pop('email', None)
        password = validated_data.pop('password', None)
        profile = validated_data.pop('profile', None)

        if not password:
            msg = 'Не передан пароль!'
            logger.error(msg)
            raise serializers.ValidationError(msg)

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
        logger.debug('Profile data: %s', profile)
        logger.debug('Profile validated data: %s', profile_serializer.validated_data)
        profile = profile_serializer.validated_data

        user: UserData = UserService.create_user(
            email,
            **validated_data,
            profile=profile
        )

        user.set_password(password)
        user.save()

        # logger.debug('UserSerializer | data: %s', self.data)
        return user


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

    def create(self, validated_data):
        logger.debug('DepartmentSerializer Validated data: %s', validated_data)
        company = validated_data.get('company')
        company_service = CompanyService(company)
        company_service.create_department(**validated_data)
