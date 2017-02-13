from django.contrib import admin
from .models import BGModel

# Register your models here.
@admin.register(BGModel)
class BGAdmin(admin.ModelAdmin):
    list_display = ('user', 'time')
    fields = ('user', 'glucose_val')

