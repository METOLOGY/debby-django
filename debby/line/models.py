from django.db import models


# Create your models here.
class EventModel(models.Model):
    phrase = models.CharField(max_length=30, blank=False)
    callback = models.CharField(max_length=30, blank=False)
    action = models.CharField(max_length=30, blank=False)
