from django.contrib import admin

from .models import Product, Comment, Discount


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'time_limit',
        'traffic_limit',
        'device_connections_limit',
        'is_special',
    ]
    list_filter = [
        'is_special',
    ]
    search_fields = [
        'name',
    ]
    list_max_show_all = 30
    list_per_page = 20


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = [
        'display_name',
        'user_city',
        'text',
    ]
    list_max_show_all = 30
    list_per_page = 20


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = [
        'value'
    ]
    list_max_show_all = 30
    list_per_page = 20