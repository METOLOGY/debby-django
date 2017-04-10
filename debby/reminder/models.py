from django.db import models
from user.models import CustomUserModel
from datetime import datetime

# Create your models here.
class UserReminder(models.Model):
    user = models.ForeignKey(CustomUserModel)
    time = models.TimeField(default=datetime.time(9, 00))
    status = models.BooleanField(default=True)
    type = models.CharField(default=True)
