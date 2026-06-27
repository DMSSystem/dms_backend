# users/serializers.py
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import User


# ── Read serializer ─────────────────────────────────────────
class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:  # type: ignore
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'role', 'phone', 'is_active', 'is_verified',
            'date_joined',
        ]
        read_only_fields = ['id', 'date_joined', 'is_verified']


# ── Unified public signup ───────────────────────────────────
class SignupSerializer(serializers.ModelSerializer):
    """
    Single public signup endpoint for parent and officer roles.
    Admin accounts cannot be self-registered.
    OTP is always sent via email — no phone option.

    Flow:
      1. POST /api/auth/signup/       → account created (inactive), OTP sent to email
      2. POST /api/auth/verify-otp/   → account activated
      3. POST /api/token/             → login and get JWT tokens
    """
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    # verification_method is always email — hidden from request body
    verification_method = serializers.HiddenField(default='email')

    # Parent-specific field
    student_admission_no = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Required if role is 'parent'. The admission number of your child."
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'role', 'phone', 'password', 'confirm_password',
            'verification_method', 'student_admission_no',
        ]

    # ── Field-level validation ──────────────────────────────

    def validate_role(self, value):
        if value == 'admin':
            raise serializers.ValidationError(
                "Administrator accounts cannot be self-registered. "
                "Contact your system administrator."
            )
        allowed = ['parent', 'officer']
        if value not in allowed:
            raise serializers.ValidationError(
                f"Role must be one of: {', '.join(allowed)}."
            )
        return value

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

    def validate_phone(self, value):
        if value:
            digits = value.replace('+', '').replace('-', '').replace(' ', '')
            if not digits.isdigit():
                raise serializers.ValidationError("Phone number must contain only digits.")
            if len(digits) < 9 or len(digits) > 15:
                raise serializers.ValidationError("Phone must be between 9 and 15 digits.")
            if User.objects.filter(phone=value).exists():
                raise serializers.ValidationError("This phone number is already registered.")
        return value

    # ── Cross-field validation ──────────────────────────────

    def validate(self, attrs):
        role = attrs.get('role')
        student_admission_no = attrs.get('student_admission_no')

        # Parents must link to a student
        if role == 'parent' and not student_admission_no:
            raise serializers.ValidationError(
                {"student_admission_no": "Admission number of your child is required for parent accounts."}
            )

        # Validate student exists
        if role == 'parent' and student_admission_no:
            from students.models import Student
            try:
                student = Student.objects.get(admission_no=student_admission_no)
                if hasattr(student, 'parent') and student.parent:
                    raise serializers.ValidationError(
                        {"student_admission_no": (
                            f"Student {student.full_name} already has a registered parent. "
                            "Contact admin if this is an error."
                        )}
                    )
                attrs['_student'] = student
            except Exception as e:
                if 'DoesNotExist' in type(e).__name__:
                    raise serializers.ValidationError(
                        {"student_admission_no": "No student found with this admission number. "
                                                 "Please contact the school."}
                    )
                raise

        # Password match + strength
        password = attrs.get('password')
        confirm = attrs.pop('confirm_password', None)
        if password != confirm:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        try:
            validate_password(password)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        return attrs

    def create(self, validated_data):
        verification_method = validated_data.pop('verification_method')
        validated_data.pop('student_admission_no', None)
        student = validated_data.pop('_student', None)
        password = validated_data.pop('password')

        user = User(
            **validated_data,
            is_active=False,
            is_verified=False,
            verification_method=verification_method,
        )
        user.set_password(password)
        user.save()

        if student:
            student.parent = user
            student.save()

        return user


# ── OTP Verification ────────────────────────────────────────
class OTPVerifySerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    otp_code = serializers.CharField(required=True, max_length=6, min_length=6)

    def validate(self, attrs):
        try:
            user = User.objects.get(username=attrs['username'])
        except User.DoesNotExist:
            raise serializers.ValidationError({"username": "User not found."})

        if user.is_verified:
            raise serializers.ValidationError("This account is already verified.")

        if user.otp_attempts >= 5:
            raise serializers.ValidationError(
                "Too many failed attempts. Request a new OTP via POST /api/auth/resend-otp/."
            )

        if not user.is_otp_valid(attrs['otp_code']):
            raise serializers.ValidationError({"otp_code": "Invalid or expired OTP code."})

        attrs['user'] = user
        return attrs


# ── Resend OTP ──────────────────────────────────────────────
class ResendOTPSerializer(serializers.Serializer):
    """Resends OTP via email only."""
    username = serializers.CharField(required=True)

    # Always email — hidden from request body
    verification_method = serializers.HiddenField(default='email')

    def validate(self, attrs):
        try:
            user = User.objects.get(username=attrs['username'])
        except User.DoesNotExist:
            raise serializers.ValidationError({"username": "User not found."})

        if user.is_verified:
            raise serializers.ValidationError("This account is already verified.")

        attrs['user'] = user
        return attrs


# ── Admin-only: create accounts directly (no OTP) ──────────
class UserCreateSerializer(serializers.ModelSerializer):
    """
    Admin only — creates accounts that are immediately active and verified.
    Used via Django admin or POST /api/users/ with admin token.
    """
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'role', 'phone', 'password', 'confirm_password',
        ]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        confirm = attrs.pop('confirm_password', None)
        if password != confirm:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        try:
            validate_password(password)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data, is_active=True, is_verified=True)
        user.set_password(password)
        user.save()
        return user


# ── Profile update ──────────────────────────────────────────
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'role', 'is_active']

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email is required.")
        qs = User.objects.filter(email__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate_role(self, value):
        request = self.context.get('request')
        if request and not request.user.is_admin:
            raise serializers.ValidationError("Only administrators can change user roles.")
        return value


# ── Password serializers ────────────────────────────────────
class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_new_password = serializers.CharField(write_only=True, required=True)

    def validate_old_password(self, value):
        if not self.context['request'].user.check_password(value):
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

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, required=True)

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value


class ForgotPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class ForgotPasswordResetSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    otp_code = serializers.CharField(required=True, min_length=6, max_length=6)
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_new_password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError({"confirm_new_password": "New passwords do not match."})

        try:
            validate_password(attrs['new_password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})

        try:
            user = User.objects.get(username=attrs['username'])
        except User.DoesNotExist:
            raise serializers.ValidationError({"username": "User not found."})

        if user.otp_attempts >= 5:
            raise serializers.ValidationError("Too many failed attempts. Please request a new code.")

        if not user.is_otp_valid(attrs['otp_code']):
            raise serializers.ValidationError({"otp_code": "Invalid or expired verification code."})

        attrs['user'] = user
        return attrs