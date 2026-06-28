from rest_framework import serializers

from .models import User


class CurrentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "phone", "role", "is_staff"]


class NannySerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=False)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "password",
            "first_name",
            "last_name",
            "email",
            "phone",
            "role",
            "is_active",
        ]
        read_only_fields = ["role"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        user.role = User.Role.NANNY
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.role = User.Role.NANNY
        if password:
            instance.set_password(password)
        instance.save()
        return instance
