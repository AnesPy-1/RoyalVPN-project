from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display =[
        'order',
        'user',
        'total_price',
        'is_used',
        'created_at',
    ]
    search_fields = ['user']
    list_filter = [
        'is_used',
    ]
    ordering = [
        '-created_at'
    ]
    list_per_page = 20
    list_max_show_all = 30

