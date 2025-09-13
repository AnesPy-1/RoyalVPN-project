from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import *


class AnswersInline(admin.TabularInline):
    model = Answer
    extra = 1
    max_num = 1


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


@admin.register(SiteSettings)
class SiteSettings(admin.ModelAdmin):
    list_display = [
        'site_name1',
        'site_name2',
    ]


@admin.register(FrequentlyAskedQuestions)
class FrequentlyAskedQuestionsAdmin(admin.ModelAdmin):
    list_display = [
        'question',
    ]
    inlines = [
        AnswersInline,
    ]