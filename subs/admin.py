from django.contrib import admin

from .models import SubscriptionLinks, Subscriptions

@admin.register(SubscriptionLinks)
class SubscriptionLinksAdmin(admin.ModelAdmin):
    list_display = [
        'plan_type',
        'day_limit',
        'traffic_limit',
        'price',
        'is_used',
    ]
    list_filter = [
        'is_used',
    ]

    list_per_page = 10
    list_max_show_all = 30

