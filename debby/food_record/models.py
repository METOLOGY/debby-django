from django.db import models

# Create your models here.


class FoodModel(models.Model):
    calories = models.IntegerField(null=True, blank=True)
    gi_value = models.IntegerField(null=True, blank=True)
    food_name = models.CharField(max_length=50)
    food_image_upload = models.ImageField(upload_to='FoodRecord')
    time = models.DateTimeField(auto_now_add=True)

