from django.contrib import admin
from .models import DrugModel, DrugDetailModel, DrugTypeModel

# Register your models here.
@admin.register(DrugModel)
class DrugModelAdmin(admin.ModelAdmin):
    list_display = (
        'chinese_name',
        'eng_name',
        'permission_type',
        'main_ingredient'
    )

@admin.register(DrugTypeModel)
class DrugDetailAdmin(admin.ModelAdmin):
    list_display = (
        'question',
        'user_choice',
        'answer',
        'type'
    )

@admin.register(DrugDetailModel)
class DrugTypeAdmin(admin.ModelAdmin):
    list_display = (
        'type',
        'mechanism',
        'side_effect',
        'taboo',
        'awareness',
    )

