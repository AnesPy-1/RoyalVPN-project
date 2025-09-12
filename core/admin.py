from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['phone', 'full_name', 'is_staff', 'is_phone_verified']
    search_fields = ['id', 'phone', 'full_name']
    ordering = ['-date_joined']
    fieldsets = (
        (None, {'fields':('phone', 'password')}),
        ('Personal', {'fields':('full_name', 'email')}),
        ('Permissions', {'fields':('is_staff', 'is_superuser', 'is_phone_verified')})
    )
    add_fieldsets = (
        (None, {
            'classes':('wide',),
            'fields': ('phone', 'password1', 'password2'),
        }),
    )