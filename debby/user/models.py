from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager
from linebot.models import TextSendMessage
from linebot.models import TemplateSendMessage
import datetime

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
        return str(self.id)


class UserSettingModel(models.Model):
    user = models.ForeignKey(CustomUserModel)
    unit = models.CharField(max_length=10,
                            choices=(
                                ('mg/dL', 'mg/dL'),
                                ('mmol/L', 'mmol/L'),
                            ),
                            default='mg/dL'
                            )

    late_reminder = models.TimeField(blank=True, null=True)
    height = models.FloatField(blank=True, null=True)
    weight = models.FloatField(blank=True, null=True)


class UserLogManger(models.Manager):
    """
    handling the logging of conversation between user and debby.
    """

    def save_to_log(self, line_id, input_text, send_message):
        if isinstance(send_message, TextSendMessage):
            log = self.model(
                user=CustomUserModel.objects.get(line_id=line_id),
                request_text=input_text,
                response=send_message.text,
            )
            log.save()
        elif isinstance(send_message, TemplateSendMessage):
            log = self.model(
                user=CustomUserModel.objects.get(line_id=line_id),
                request_text=input_text,
                response=send_message.alt_text,
            )
            log.save()


class UserLogModel(models.Model):
    user = models.ForeignKey(CustomUserModel)
    request_text = models.CharField(max_length=1000,
                                    verbose_name=('Request from user.'))
    response = models.CharField(max_length=1000,
                                verbose_name=('Response from debby.'))
    time = models.DateTimeField(auto_now_add=True)

    objects = UserLogManger()
