from django.contrib import admin

from .models import BotPaymentRequest, BotRequestLog, BotSession, WalletTransaction
from .services import approve_payment_request, reject_payment_request


@admin.register(BotSession)
class BotSessionAdmin(admin.ModelAdmin):
    list_display = ["user", "telegram_user_id", "is_active", "expires_at", "last_used_at"]
    list_filter = ["is_active"]
    search_fields = ["user__username", "user__full_name", "telegram_user_id"]
    ordering = ["-created_at"]


@admin.register(BotPaymentRequest)
class BotPaymentRequestAdmin(admin.ModelAdmin):
    list_display = ["reference_id", "user", "requested_amount", "payable_amount", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["reference_id", "user__username", "user__full_name", "transaction_id"]
    ordering = ["-created_at"]
    readonly_fields = ["reference_id", "created_at", "updated_at", "approved_transaction"]
    actions = ["mark_selected_approved", "mark_selected_rejected"]

    @admin.action(description="Approve selected requests")
    def mark_selected_approved(self, request, queryset):
        for item in queryset.select_related("user"):
            if item.status == BotPaymentRequest.Status.PENDING:
                approve_payment_request(payment_request=item, approved_by=request.user)

    @admin.action(description="Reject selected requests")
    def mark_selected_rejected(self, request, queryset):
        for item in queryset.select_related("user"):
            if item.status == BotPaymentRequest.Status.PENDING:
                reject_payment_request(payment_request=item, approved_by=request.user)


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ["user", "kind", "amount", "previous_balance", "new_balance", "created_at"]
    list_filter = ["kind", "created_at"]
    search_fields = ["user__username", "reference_code", "note"]
    ordering = ["-created_at"]


@admin.register(BotRequestLog)
class BotRequestLogAdmin(admin.ModelAdmin):
    list_display = ["endpoint", "method", "ip_address", "status_code", "user", "created_at"]
    list_filter = ["method", "status_code", "created_at"]
    search_fields = ["endpoint", "ip_address", "user__username"]
    ordering = ["-created_at"]
