from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'get_full_name', 'role', 'supervisor', 'phone', 'is_online', 'is_active')
    list_filter = ('role', 'is_online', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'phone')

    fieldsets = BaseUserAdmin.fieldsets + (
        ('اطلاعات CRM', {
            'fields': ('role', 'supervisor', 'phone', 'is_online', 'max_capacity', 'avatar', 'bio')
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('اطلاعات CRM', {
            'fields': ('role', 'supervisor', 'phone', 'max_capacity')
        }),
    )
