from django.db import models
from user.models import CustomUserModel


class BGModel(models.Model):
    user = models.ForeignKey(CustomUserModel, related_name='user')
    time = models.DateTimeField(auto_now_add=True)
    glucose_val = models.IntegerField(blank=False)

    def __str__(self):
        return self.user.line_id
