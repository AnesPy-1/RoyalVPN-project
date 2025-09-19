from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from orders.models import Order
from payment.models import Payment
from subs.models import Subscriptions
from .models import *

class PaymentsInline(admin.TabularInline):
    model = Payment
    extra = 0


class SubscriptionInline(admin.TabularInline):
    model = Subscriptions
    extra = 0


class OrdersInline(admin.TabularInline):
    model = Order
    extra = 0

class AnswersInline(admin.TabularInline):
    model = Answer
    extra = 1
    max_num = 1


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'full_name', 'is_staff']
    search_fields = ['id', 'phone', 'full_name']
    ordering = ['-date_joined']
    fieldsets = (
        (None, {'fields':('username', 'password')}),
        ('Personal', {'fields':('full_name', 'email', 'telegram_id')}),
        ('Permissions', {'fields':('is_staff', 'is_superuser')})
    )
    add_fieldsets = (
        (None, {
            'classes':('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )
    inlines = [
        PaymentsInline,
        SubscriptionInline,
        OrdersInline,
    ]


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
