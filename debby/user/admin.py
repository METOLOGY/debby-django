from django.contrib import admin
from .models import CustomUserModel

# Register your models here.
@admin.register(CustomUserModel)
class CustomUserAdmin(admin.ModelAdmin):
    date_hierarchy = 'date_joined'
    fields = ('lineID', 'username', 'date_joined')