import uuid

from django.db import models
from django.utils.text import gettext_lazy as _
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("email is required")

        for key, value in extra_fields.items():
            if isinstance(value, str):
                extra_fields[key] = value.title()

        normalized_email = self.normalize_email(email)
        user = self.model(email=normalized_email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if not extra_fields['is_superuser']:
            raise ValueError("super user field must be set")
        if not extra_fields['is_staff']:
            raise ValueError("is-staff field must be set")

        user = self.create_user(email=email, password=password, **extra_fields)
        return user

class CustomUser(AbstractBaseUser):

    objects = CustomUserManager()

    user_id = models.UUIDField(
        primary_key=True, db_index=True, editable=False,
        unique=True, default=uuid.uuid4)

    email = models.EmailField(unique=True, max_length=255, db_index=True)

    username = models.CharField(max_length=255, unique=True, db_index=True)

    avatar = models.URLField(max_length=500, blank=True, null=True)

    date_joined  = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    is_superuser = models.BooleanField(default=False, db_index=True)
    is_staff = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def get_display_name(self):
        return self.username.title()

    def __str__(self):
        return f"{self.email} {self.user_id}"

    class Meta:
        verbose_name = _("CustomUser")
        verbose_name_plural = _("Custom users")
        indexes = [
            models.Index(fields=['is_active'])

        ]



