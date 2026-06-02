"""Serializers for accounts: registration, login, profile management."""

from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    """Customer self-registration. Account begins in PENDING state."""

    password  = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, label="Confirm password")

    class Meta:
        model  = User
        fields = [
            "email", "first_name", "last_name",
            "phone", "password", "password2",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password2"):
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(
            role           = User.Role.CUSTOMER,
            account_status = User.AccountStatus.PENDING,
            **validated_data,
        )


class LoginSerializer(serializers.Serializer):
    """Authenticate a user and return the user instance."""

    email    = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        user = authenticate(username=attrs["email"], password=attrs["password"])

        if not user:
            raise serializers.ValidationError("Invalid email or password.")

        if user.is_customer and not user.is_approved:
            raise serializers.ValidationError(
                "Your account is awaiting admin approval."
            )

        attrs["user"] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Read / update a user's own profile."""

    full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model  = User
        fields = [
            "id", "email", "first_name", "last_name",
            "phone", "profile_picture", "role",
            "account_status", "full_name", "date_joined",
        ]
        read_only_fields = ["id", "email", "role", "account_status", "date_joined"]

    def get_full_name(self, obj):
        return obj.get_full_name()


class ChangePasswordSerializer(serializers.Serializer):
    """Allow an authenticated user to change their own password."""

    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class AdminUserListSerializer(serializers.ModelSerializer):
    """Summary view of any user — used by Admin endpoints."""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = [
            "id", "email", "full_name", "role",
            "account_status", "date_joined", "admin_notes",
        ]
        read_only_fields = fields

    def get_full_name(self, obj):
        return obj.get_full_name()
