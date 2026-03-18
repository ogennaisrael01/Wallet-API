
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

UserModel = get_user_model()
import validators


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for reading user data.
    Used for profile retrieval and user listing.
    """

    display_name = serializers.SerializerMethodField(read_only=True)
    user_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = UserModel
        fields = [
            "user_id", "email",
            "avatar", "is_active",
            "date_joined", "display_name",
            "updated_at",
        ]
        read_only_fields = ["user_id", "date_joined", "updated_at"]

    def get_display_name(self, obj):
        """Get user's full name."""
        return obj.get_display_name()

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Validates email, password, and creates a new user.
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        help_text="Password must be at least 8 characters long and include uppercase, lowercase, and numbers.",
    )

    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        help_text="Password confirmation",
    )

    email = serializers.EmailField(required=True)

    class Meta:
        model = UserModel
        fields = ["email", "username", "password", "password_confirm"]

    def validate_email(self, value):
        """
        Validate that email is unique.
        """
        if UserModel.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate_password(self, value):

        # Django's built-in password validator
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)

        # Additional custom validation
        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long."
            )

        return value

    def validate(self, data):
        """
        Validate that passwords match.
        """
        if data.get("password") != data.get("password_confirm"):
            raise serializers.ValidationError(
                {"password": "Passwords do not match."}
            )
        return data

    def create(self, validated_data):
        """
        Create a new user with the validated data.
        """
        # Remove password_confirm from validated data
        validated_data.pop("password_confirm")

        # Create user
        user = UserModel.objects.create_user(**validated_data)

        return user

class UserLoginSerializer(TokenObtainPairSerializer):
    """
    Custom login serializer extending SimpleJWT's TokenObtainPairSerializer.
    Allows login with email instead of username.
    """

    username_field = UserModel.USERNAME_FIELD  # email

    def validate(self, attrs):
        """
        Override validate to use email field.
        """
        # Extract email and password
        email = attrs.get(self.username_field)
        password = attrs.get("password")

        # Try to get user by email
        try:
            user = UserModel.objects.get(email__iexact=email)
        except UserModel.DoesNotExist:
            raise serializers.ValidationError(
                {"detail": "Invalid email or password."}
            )

        # Check if user is active
        if not user.is_active:
            raise serializers.ValidationError(
                {"detail": "User account is disabled."}
            )

        # Verify password
        if not user.check_password(password):
            raise serializers.ValidationError(
                {"detail": "Invalid email or password."}
            )

        # Update last login
        user.save(update_fields=["last_login"])

        # Call parent validate to get tokens
        data = super().validate(attrs)

        data.update({
            "user_id": user.pk
        })
        return data

    @classmethod
    def get_token(cls, user):
        """
        Generate token with custom claims.
        """
        token = super().get_token(user)

        # Add custom claims
        token["email"] = user.email
        token["username"] = user.username

        return token

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = [
            "user_id", "username",
            "avatar",
        ]
        read_only_fields = ['user_id']

    def validated(self, data):
        if "email" or "password" in data:
            raise serializers.ValidationError("You cannot update email and password")
        return data
    def validate_username(self, value):
        if not isinstance(value, str):
            raise serializers.ValidationError("only str instance is required")
        return value.title()

    def validated_avatar(self, value):
        if not validators.url(value):
            raise serializers.ValidationError("this is  not a valid url for profile avatar")
        return value.strip()

    def update(self, instance:UserModel, validated_data: dict):
        user = self.context.get("request").user

        if instance.email != user.email:
            raise PermissionDenied()

        updated_user = super().update(instance, validated_data)
        return updated_user

