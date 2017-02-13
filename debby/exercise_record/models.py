from django.db import models


# Create your models here.

class Exercise(models.Model):
    type = models.CharField()
    start_from = models.DateTimeField()
    duration = models.IntegerField()
