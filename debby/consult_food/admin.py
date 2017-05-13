from django.contrib import admin
from .models import ConsultFoodModel


# Register your models here.
@admin.register(ConsultFoodModel)
class ConsultFoodAdmin(admin.ModelAdmin):
    list_display = ('sample_name', 'modified_calorie',
                    'carbohydrates', 'dietary_fiber',
                    'metabolic_carbohydrates', 'carbohydrates_equivalent',
                    'white_rice_equivalent')
    fields = ('sample_name', 'modified_calorie',
              'carbohydrates', 'dietary_fiber',
              'metabolic_carbohydrates', 'carbohydrates_equivalent',
              'white_rice_equivalent')
