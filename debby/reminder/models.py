from django.db import models
from user.models import CustomUserModel
import datetime


# reminder number should be limited. 5 reminder for each type, maximum.
class UserReminder(models.Model):
    user = models.ForeignKey(CustomUserModel)
    time = models.TimeField(default=datetime.time(9, 00))
    status = models.BooleanField(default=True)
    type = models.CharField(default=True, max_length=10, choices=(
        ('bg', 'blood sugar'),
        ('insulin', 'insulin'),
        ('drug', 'drug')
    ))
