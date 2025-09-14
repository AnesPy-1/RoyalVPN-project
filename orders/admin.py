from django.contrib import admin

from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'phone_number',
        'name',
    ]
    list_filter = [
        'status'
    ]
    search_fields = [
        'id',
        'user',
        'name',
    ]
    ordering = [
        'created_at',
    ]
    autocomplete_fields = [
        'user'
    ]
    list_max_show_all = 30
    list_per_page = 20

    inlines = [
        OrderItemInline,
    ]