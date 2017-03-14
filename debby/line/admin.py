from django.contrib import admin
from .models import EventModel


# Register your models here.
@admin.register(EventModel)
class Eventdmin(admin.ModelAdmin):
    list_display = ['phrase', 'callback', 'action']
