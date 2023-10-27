import logging

from django.conf import settings
from rest_framework import serializers

from apps.authorization.models import (
    UserData,
    CompanyProfile,
    WorkerProfile,
    TenantProfile,
    Department,
    CustomPermissionModel
)


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


class UserRegistrationSerializer(serializers.Serializer):
    """Валидация данных пользователя при регистрации"""
    email = serializers.EmailField(max_length=100)
    password = serializers.CharField(max_length=128, write_only=True)
    profile = serializers.JSONField()

    def validate_profile(self, profile: dict):
        """Валидация поля профиля"""
        logger.debug('validate_profile | Profile data: %s', profile)

        user_type = profile.get('type')
        if user_type == settings.ORG:
            profile_serializer = CompanyProfileSerializer(data=profile)
        elif user_type == settings.WORKER:
            profile_serializer = WorkerProfileSerializer(data=profile)
        elif user_type == settings.TENANT:
            profile_serializer = TenantProfileSerializer(data=profile)
        else:
            msg = 'Передан не верный тип профиля пользователя (в "profiles")!'
            logger.error(msg)
            raise serializers.ValidationError(detail=msg)

        profile_serializer.is_valid(raise_exception=True)

        logger.debug('validate_profile | Profile validated data: %s',
                     profile_serializer.validated_data)

        return profile


class UserEditSerializer(serializers.ModelSerializer):
    """Сериалайзер для валидации данных при изменении данных о пользователе"""

    class Meta:
        model = UserData
        exclude = ['user_permissions', 'groups', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True},
            'activation_code': {'write_only': True},
        }


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomPermissionModel
        fields = '__all__'


class PermissionCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(max_length=255, required=False)


class PermissionEditSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    new_name = serializers.CharField(max_length=100, required=False)
    description = serializers.CharField(max_length=255, required=False)
    new_description = serializers.CharField(max_length=255, required=False)
