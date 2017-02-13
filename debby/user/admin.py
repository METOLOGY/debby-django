from django.contrib import admin
from .models import CustomUserModel

# Register your models here.
@admin.register(CustomUserModel)
class CustomUserAdmin(admin.ModelAdmin):
    date_hierarchy = 'date_joined'
    list_display = ('line_id', 'username', 'date_joined')
    fields = ('line_id', 'username', 'date_joined')