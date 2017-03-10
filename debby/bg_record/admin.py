from django.contrib import admin
from .models import BGModel

# Register your models here.
@admin.register(BGModel)
class BGAdmin(admin.ModelAdmin):
    list_display = ('user', 'glucose_val', 'time', 'type')
    fields = ('user', 'glucose_val', 'type')

