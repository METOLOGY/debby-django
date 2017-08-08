from django.contrib import admin

from .models import TaiwanSnackModel


@admin.register(TaiwanSnackModel)
class TaiwanSnackFoodAdmin(admin.ModelAdmin):
    list_display = ('name', 'count_word')
