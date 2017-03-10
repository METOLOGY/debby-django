from django.contrib import admin
from .models import QAModel

# Register your models here.
@admin.register(QAModel)
class QAAdmin(admin.ModelAdmin):
    list_display = ['phrase', 'answer', 'callback']
