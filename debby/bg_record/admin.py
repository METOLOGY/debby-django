from django.contrib import admin
from .models import BGModel, InsulinIntakeModel, DrugIntakeModel

# Register your models here.
@admin.register(BGModel)
class BGAdmin(admin.ModelAdmin):
    list_display = ('user', 'glucose_val', 'time', 'type')
    fields = ('user', 'glucose_val', 'type')

@admin.register(InsulinIntakeModel)
class InsulinIntakeAdmin(admin.ModelAdmin):
    list_display = ('user', 'time', 'status', )
    fields = ('user', 'time', 'status')


@admin.register(DrugIntakeModel)
class DrugIntakeAdmin(admin.ModelAdmin):
    list_display = ('user', 'time', 'status',)
    fields = ('user', 'time', 'status')
