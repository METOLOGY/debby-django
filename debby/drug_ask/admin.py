from django.contrib import admin
from .models import DrugModel

# Register your models here.
@admin.register(DrugModel)
class DrugAskAdmin(admin.ModelAdmin):
    list_display = (
        'chinese_name',
        'eng_name',
        'permission_type',
        'main_ingredient'
    )