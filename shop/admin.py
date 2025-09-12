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
    list_per_page = 10
    list_max_show_all = 30


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = [
        'display_name',
        'user_city',
        'text',
    ]
    list_per_page = 10
    list_max_show_all = 30


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = [
        'value'
    ]