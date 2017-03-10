from django.contrib import admin
from .models import CustomUserModel

# Register your models here.
@admin.register(CustomUserModel)
class CustomUserAdmin(admin.ModelAdmin):
    date_hierarchy = 'date_joined'
    list_display = ('line_id', 'first_name', 'last_name', 'date_joined')
    fieldsets = (
        (None, {'fields': ('line_id', 'email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ['date_joined']}),
    )

    readonly_fields = (
        'date_joined',
    )

class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'unit', 'breakfast_reminder', 'lunch_reminder', 'dinner_reminder')
    fieldsets = (
        ('基本資料', {'fields': ('user','height', 'weight')}),
        ('血糖單位', {'fields': ('unit')}),
        ('早餐血糖紀錄提醒', {'fields': ('breakfast_reminder_status', 'breakfast_reminder')}),
        ('午餐血糖紀錄提醒', {'fields': ('lunch_reminder_status', 'lunch_reminder')}),
        ('晚餐血糖紀錄提醒', {'fields': ('dinner_reminder_status', 'dinner_reminder')}),
        ('延後提醒時間', {'fields': ('late_reminder')}),
    )

    readonly_fields = ('user')