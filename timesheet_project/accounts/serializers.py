from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User
from .services import (
    GENERIC_SETUP_REQUEST_MESSAGE,
    generate_pending_username,
    get_available_account_setup_token,
    send_setup_email_for_identifier,
)


class CurrentUserSerializer(serializers.ModelSerializer):
    can_access_dashboard = serializers.BooleanField(read_only=True)
    can_access_django_admin = serializers.BooleanField(read_only=True)
    account_setup_required = serializers.BooleanField(read_only=True)

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
            "account_setup_required",
            "can_access_dashboard",
            "can_access_django_admin",
        ]


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        validate_password(attrs["new_password"], self.context["request"].user)
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.force_password_change = False
        user.save(update_fields=["password", "force_password_change"])
        return user


class ManagedUserSerializerMixin:
    def validate_email(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Email is required.")
        return value

    def validate_phone(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Phone is required.")
        return value

    def create_pending_user(self, validated_data, role):
        validated_data.pop("password", None)
        validated_data.pop("force_password_change", None)
        user = User(**validated_data)
        user.username = generate_pending_username()
        user.role = role
        user.is_staff = False
        user.is_superuser = False
        user.force_password_change = False
        user.set_unusable_password()
        user.save()
        return user

    def update_profile(self, instance, validated_data):
        validated_data.pop("password", None)
        validated_data.pop("force_password_change", None)
        for attr, value in validated_data.items():
            if attr == "is_staff":
                continue
            setattr(instance, attr, value)
        instance.save()
        return instance


class NannySerializer(ManagedUserSerializerMixin, serializers.ModelSerializer):
    account_setup_required = serializers.BooleanField(read_only=True)

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
            "account_setup_required",
        ]
        read_only_fields = ["username", "role", "account_setup_required"]

    def create(self, validated_data):
        return self.create_pending_user(validated_data, User.Role.NANNY)

    def update(self, instance, validated_data):
        instance.role = User.Role.NANNY
        return self.update_profile(instance, validated_data)


class DashboardUserSerializer(ManagedUserSerializerMixin, serializers.ModelSerializer):
    can_access_dashboard = serializers.BooleanField(read_only=True)
    can_access_django_admin = serializers.BooleanField(read_only=True)
    account_setup_required = serializers.BooleanField(read_only=True)

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
            "account_setup_required",
            "can_access_dashboard",
            "can_access_django_admin",
        ]
        read_only_fields = ["username", "is_staff", "account_setup_required"]

    def validate_role(self, value):
        if value not in {User.Role.OFFICE, User.Role.ADMIN}:
            raise serializers.ValidationError("Dashboard users must have the office or admin role.")
        return value

    def create(self, validated_data):
        return self.create_pending_user(validated_data, validated_data.get("role"))

    def update(self, instance, validated_data):
        return self.update_profile(instance, validated_data)


class AccountSetupRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField(write_only=True, allow_blank=False)
    detail = serializers.CharField(read_only=True)

    def save(self, **kwargs):
        send_setup_email_for_identifier(self.validated_data["identifier"])
        return {"detail": GENERIC_SETUP_REQUEST_MESSAGE}


class AccountSetupValidateSerializer(serializers.Serializer):
    token = serializers.CharField(write_only=True, allow_blank=False)

    def validate_token(self, value):
        setup_token = get_available_account_setup_token(value)
        if setup_token is None:
            raise serializers.ValidationError("Setup link is invalid or expired.")
        return value

    def to_representation(self, instance):
        setup_token = get_available_account_setup_token(self.validated_data["token"])
        user = setup_token.user
        return {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": user.phone,
            "role": user.role,
        }


class AccountSetupCompleteSerializer(serializers.Serializer):
    token = serializers.CharField(write_only=True, allow_blank=False)
    username = serializers.CharField(write_only=True, allow_blank=False)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_username(self, value):
        value = value.strip()
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate(self, attrs):
        setup_token = get_available_account_setup_token(attrs["token"])
        if setup_token is None:
            raise serializers.ValidationError({"token": "Setup link is invalid or expired."})
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        validate_password(attrs["password"], setup_token.user)
        attrs["setup_token"] = setup_token
        return attrs

    def save(self, **kwargs):
        setup_token = self.validated_data["setup_token"]
        user = setup_token.user
        user.username = self.validated_data["username"]
        user.set_password(self.validated_data["password"])
        user.force_password_change = False
        user.save(update_fields=["username", "password", "force_password_change"])
        setup_token.mark_used()
        return user
