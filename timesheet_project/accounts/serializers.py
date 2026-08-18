from rest_framework import serializers

from .models import User


class CurrentUserSerializer(serializers.ModelSerializer):
    can_access_dashboard = serializers.BooleanField(read_only=True)
    can_access_django_admin = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "role",
            "is_active",
            "is_staff",
            "force_password_change",
            "can_access_dashboard",
            "can_access_django_admin",
        ]


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
            "force_password_change",
        ]
        read_only_fields = ["role"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        user.role = User.Role.NANNY
        if password:
            user.set_password(password)
            user.force_password_change = validated_data.get("force_password_change", True)
        else:
            user.set_unusable_password()
            user.force_password_change = True
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.role = User.Role.NANNY
        if password:
            instance.set_password(password)
            instance.force_password_change = True
        instance.save()
        return instance


class DashboardUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=False)
    can_access_dashboard = serializers.BooleanField(read_only=True)
    can_access_django_admin = serializers.BooleanField(read_only=True)

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
            "is_staff",
            "force_password_change",
            "can_access_dashboard",
            "can_access_django_admin",
        ]
        read_only_fields = ["is_staff"]

    def validate_role(self, value):
        if value not in {User.Role.OFFICE, User.Role.ADMIN}:
            raise serializers.ValidationError("Dashboard users must have the office or admin role.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        user.is_staff = False
        if password:
            user.set_password(password)
            user.force_password_change = validated_data.get("force_password_change", True)
        else:
            user.set_unusable_password()
            user.force_password_change = True
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            if attr == "is_staff":
                continue
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
            instance.force_password_change = True
        instance.is_staff = False if not instance.is_superuser else instance.is_staff
        instance.save()
        return instance
