from django.db import models


# Create your models here.

class ChatModel(models.Model):
    phrase = models.CharField(max_length=120, blank=True)
    answer = models.CharField(max_length=120, blank=True)
