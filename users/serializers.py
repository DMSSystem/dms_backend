# users/serializers.py
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Read serializer — used for listing and retrieving users.
    Never exposes password.
    """
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'role', 'phone', 'is_active', 'date_joined',
        ]
        read_only_fields = ['id', 'date_joined']


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Write serializer — used by admins to create new users.
    Handles password hashing and role assignment.
    """
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'role', 'phone', 'password', 'confirm_password',
        ]

    # ── Field-level validation ──────────────────────────────
    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email is required.")
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_role(self, value):
        allowed = [r[0] for r in User.ROLE_CHOICES]
        if value not in allowed:
            raise serializers.ValidationError(
                f"Invalid role. Must be one of: {', '.join(allowed)}."
            )
        return value

    def validate_phone(self, value):
        if value:
            digits = value.replace('+', '').replace('-', '').replace(' ', '')
            if not digits.isdigit():
                raise serializers.ValidationError("Phone number must contain only digits.")
            if len(digits) < 9 or len(digits) > 15:
                raise serializers.ValidationError("Phone number must be between 9 and 15 digits.")
        return value

    # ── Cross-field validation ──────────────────────────────
    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.pop('confirm_password', None)

        if password != confirm_password:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        # Run Django's built-in password validators (length, common passwords, etc.)
        try:
            validate_password(password)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)  # Hashes the password
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Update serializer — allows users to update their own profile,
    and admins to update any user's details (excluding password).
    """
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'role', 'is_active']

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email is required.")
        qs = User.objects.filter(email__iexact=value).exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate_role(self, value):
        # Only admins can change roles — enforced at view level too
        request = self.context.get('request')
        if request and not request.user.is_admin:
            raise serializers.ValidationError("Only administrators can change user roles.")
        return value


class PasswordChangeSerializer(serializers.Serializer):
    """
    Allows a user to change their own password.
    """
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_new_password = serializers.CharField(write_only=True, required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError(
                {"confirm_new_password": "New passwords do not match."}
            )
        try:
            validate_password(attrs['new_password'], self.context['request'].user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})
        return attrs

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetSerializer(serializers.Serializer):
    """
    Allows an admin to reset any user's password directly.
    """
    new_password = serializers.CharField(write_only=True, required=True)

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value