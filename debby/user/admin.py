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
