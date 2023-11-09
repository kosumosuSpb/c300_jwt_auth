import logging

from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.authorization.models import (
    UserData,
    UserProfile,
    CompanyProfile,
    WorkerProfile,
    TenantProfile,
    Department,
    PermissionModel
)


logger = logging.getLogger(__name__)


def get_profile_serializer(profile_type: str):
    """По введённому типу профиля возвращает его сериалайзер"""
    match profile_type:
        case settings.ORG:
            profile_serializer = CompanyProfileSerializer
        case settings.WORKER:
            profile_serializer = WorkerProfileSerializer
        case settings.TENANT:
            profile_serializer = TenantProfileSerializer
        case _:
            msg = 'Передан не верный тип профиля пользователя (в "profiles")!'
            logger.error(msg)
            raise serializers.ValidationError(detail=msg)

    return profile_serializer


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
    """Валидация данных пользователя при регистрации и выводе данных о пользователе"""
    email = serializers.EmailField(max_length=100)
    password = serializers.CharField(max_length=128, write_only=True)
    profile = serializers.JSONField()

    def validate_profile(self, profile: dict):
        """Валидация поля профиля"""
        logger.debug('validate_profile | Profile data: %s', profile)

        user_type = profile.get('type')

        profile_serializer_class = get_profile_serializer(user_type)
        profile_serializer = profile_serializer_class(data=profile)

        try:
            profile_serializer.is_valid(raise_exception=True)
        except ValidationError as ve:
            logger.error('Ошибка валидации профиля %s', ve)
            raise

        logger.debug('validate_profile | Profile validated data: %s',
                     profile_serializer.validated_data)

        return profile


class ProfileField(serializers.RelatedField):
    """Описание валидации поля профиля"""
    queryset = UserData.objects.all()

    def to_representation(self, profile: UserProfile):
        logger.debug('ProfileField | to_representation | value: %s', profile)

        user_type = profile.type

        profile_serializer_class = get_profile_serializer(user_type)
        profile_serializer = profile_serializer_class(profile)

        return profile_serializer.data

    def to_internal_value(self, profile: dict):
        logger.debug('ProfileField | to_internal_value | data: %s', profile)

        user_type = profile.get('type')

        profile_serializer_class = get_profile_serializer(user_type)
        profile_serializer = profile_serializer_class(data=profile)

        try:
            profile_serializer.is_valid(raise_exception=True)
        except ValidationError as ve:
            logger.error('Ошибка валидации профиля %s', ve)
            raise

        logger.debug('ProfileField | to_internal_value | validated data: %s',
                     profile_serializer.validated_data)

        return profile


class UserEditSerializer(serializers.ModelSerializer):
    """Сериалайзер для валидации информации о пользователе при редактировании"""
    profile = ProfileField()

    class Meta:
        model = UserData
        exclude = ['user_permissions', 'groups', 'password']
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
        model = PermissionModel
        exclude = ['workers', 'tenants', 'companies']


class PermissionCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(max_length=255, required=False)
