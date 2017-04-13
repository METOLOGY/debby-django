from django.contrib import admin
from .models import UserReminder

# Register your models here.
@admin.register(UserReminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ('user', 'time', 'status', 'type')
    fields = ('user', 'time', 'status', 'type')