from django.db import models


# Create your models here.

class Exercise(models.Model):
    type = models.CharField(max_length=100)
    start_from = models.DateTimeField()
    duration = models.IntegerField()
