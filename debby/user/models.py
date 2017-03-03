from django.db import models
from django.contrib.auth.models import AbstractUser, User, Group, PermissionsMixin, BaseUserManager

# Custom user model for line.
# example from https://www.caktusgroup.com/blog/2013/08/07/migrating-custom-user-model-django/

class CustomUserManager(BaseUserManager):
    def _create_user(self, line_id, password, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not line_id:
            raise ValueError('no line_id was given. failed to create user.')
        user = self.model(line_id=line_id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, line_id=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(line_id, password, **extra_fields)

    def create_superuser(self, line_id, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(line_id, password, **extra_fields)


class CustomUserModel(AbstractUser):
    username_validator = None
    username = None

    line_id = models.CharField(max_length=33, unique=True)
    line_token = models.CharField(max_length=100, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'line_id'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return self.line_id
