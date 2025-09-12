from django.contrib import admin

from .models import SubscriptionLinks, Subscriptions

@admin.register(SubscriptionLinks)
class SubscriptionLinksAdmin(admin.ModelAdmin):
    list_display = [
        'plan_type',
        'day_limit',
        'traffic_limit',
        'is_used',
    ]
    list_filter = [
        'is_used',
    ]

    list_per_page = 10
    list_max_show_all = 30


@admin.register(Subscriptions)
class SubscriptionsAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'sub',
        'is_test',
        'expire_date',
    ]
    list_filter = [
        'is_test',
    ]
    search_fields = [
        'user',
    ]
    list_per_page = 10
    list_max_show_all = 30