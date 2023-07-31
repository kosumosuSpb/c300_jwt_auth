import logging

from rest_framework import serializers

from .models import UserData


logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserData
        # fields = ["email", "name", "password", "username"]
        # fields = '__all__'
        exclude = ['user_permissions', 'groups']

    def create(self, validated_data):
        logger.debug('UserSerializer - Validated data: %s', validated_data)
        # user = UserData.objects.create(email=validated_data['email'], name=validated_data['name'])

        pwd = validated_data.pop('password', None)
        user = UserData.objects.create(**validated_data)

        if not pwd:
            msg = 'Создание пароля не реализовано'
            logger.error(msg)
            raise NotImplementedError(msg)

        user.set_password(pwd)
        user.save()
        return user
