from django.contrib import admin
from .models import FoodModel


# Register your models here.
@admin.register(FoodModel)
class FoodAdmin(admin.ModelAdmin):
    list_display = ('user', 'food_image_upload', 'note', 'time', )
    fields = ('user', 'food_image_upload', 'note', 'time', )