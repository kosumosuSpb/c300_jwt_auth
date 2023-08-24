import logging

from rest_framework import serializers

from app.authorization.models import (
    UserData,
    CompanyProfile,
    WorkerProfile,
    TenantProfile,
)
from app.authorization.services.user_service import UserService


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

    def create(self, validated_data):
        logger.debug('UserSerializer - Validated data: %s', validated_data)

        email = validated_data.pop('email', None)
        password = validated_data.pop('password', None)
        profile = validated_data.pop('profile', None)

        if not password:
            msg = 'Не передан пароль!'
            logger.error(msg)
            raise serializers.ValidationError(msg)

        if not profile:
            msg = 'Не передан обязательный атрибут "profile"!'
            logger.error(msg)
            raise serializers.ValidationError(detail=msg)

        if not isinstance(profile, dict):
            msg = 'Не верный тип аргумента "profile"!'
            logger.error(msg)
            raise serializers.ValidationError(detail=msg)

        user_type = profile.pop('type', None)
        # TODO: добавить поле типа в профили, чтобы его можно было сериализовать?
        if user_type == UserData.ORG:
            profile_serializer = CompanyProfileSerializer(data=profile)
        elif user_type == UserData.WORKER:
            profile_serializer = WorkerProfileSerializer(data=profile)
        elif user_type == UserData.TENANT:
            profile_serializer = TenantProfileSerializer(data=profile)
        else:
            msg = 'Передан не верный тип профиля пользователя (в "profiles")!'
            logger.error(msg)
            raise serializers.ValidationError(detail=msg)

        profile_serializer.is_valid(raise_exception=True)
        logger.debug('Profile data: %s', profile)
        logger.debug('Profile validated data: %s', profile_serializer.validated_data)
        profile = profile_serializer.validated_data

        user = UserService.create_user(email, **validated_data, profile=profile)

        user.set_password(password)
        user.save()
        return user
