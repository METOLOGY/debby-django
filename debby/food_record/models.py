from django.db import models

# Create your models here.
from user.models import CustomUserModel


class FoodModel(models.Model):
    user = models.ForeignKey(CustomUserModel)
    calories = models.IntegerField(null=True, blank=True)
    gi_value = models.IntegerField(null=True, blank=True)
    food_name = models.CharField(max_length=50)
    food_image_upload = models.ImageField(upload_to='FoodRecord')
    note = models.CharField(max_length=200)
    time = models.DateTimeField(auto_now_add=True)


