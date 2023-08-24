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
        fields = '__all__'


class WorkerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerProfile
        fields = '__all__'


class TenantProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantProfile
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    profile = serializers.JSONField()

    class Meta:
        model = UserData
        exclude = ['user_permissions', 'groups']

    def create(self, validated_data):
        logger.debug('UserSerializer - Validated data: %s', validated_data)
        # user = UserData.objects.create(email=validated_data['email'], name=validated_data['name'])

        password = validated_data.pop('password', None)
        profile = validated_data.pop('profile', None)

        if not profile:
            msg = 'Не передан обязательный атрибут "profile"!'
            logger.error(msg)
            raise serializers.ValidationError(detail=msg)

        if not isinstance(profile, dict):
            msg = 'Не верный тип аргумента "profile"!'
            logger.error(msg)
            raise serializers.ValidationError(detail=msg)

        user_type = profile.pop('type', None)
        if user_type == UserData.ORG:
            pass
        elif user_type == UserData.WORKER:
            pass
        elif user_type == UserData.TENANT:
            pass
        else:
            msg = 'Передан не верный тип профиля пользователя (в "profiles")!'
            logger.error(msg)
            raise serializers.ValidationError(detail=msg)

        user = UserService.create_user(user_type, profile=profile)

        if not password:
            msg = 'Создание пароля не реализовано'
            logger.error(msg)
            raise NotImplementedError(msg)

        user.set_password(password)
        user.save()
        return user
