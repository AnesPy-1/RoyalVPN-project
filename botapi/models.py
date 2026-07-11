import hashlib
from datetime import timedelta
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class BotSession(models.Model):
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="bot_sessions",
        verbose_name=_("user"),
    )
    token_hash = models.CharField(_("token hash"), max_length=128, unique=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    last_used_at = models.DateTimeField(_("last used at"), auto_now=True)
    expires_at = models.DateTimeField(_("expires at"))
    is_active = models.BooleanField(_("is active"), default=True)
    telegram_user_id = models.CharField(_("telegram user id"), max_length=64, blank=True)

    class Meta:
        verbose_name = _("Bot session")
        verbose_name_plural = _("Bot sessions")
        indexes = [
            models.Index(fields=["token_hash"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"bot session for {self.user_id}"

    @staticmethod
    def make_token() -> str:
        return secrets.token_urlsafe(40)

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @classmethod
    def issue(cls, *, user, telegram_user_id: str = "", ttl_hours: int | None = None):
        ttl_hours = ttl_hours or getattr(settings, "BOT_SESSION_TTL_HOURS", 24)
        token = cls.make_token()
        obj = cls.objects.create(
            user=user,
            token_hash=cls.hash_token(token),
            expires_at=timezone.now() + timedelta(hours=ttl_hours),
            telegram_user_id=telegram_user_id,
        )
        return token, obj

    def is_expired(self) -> bool:
        return not self.is_active or self.expires_at <= timezone.now()


class BotPaymentRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        APPROVED = "approved", _("Approved")
        REJECTED = "rejected", _("Rejected")

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="bot_payment_requests",
        verbose_name=_("user"),
    )
    reference_id = models.CharField(_("reference id"), max_length=6, unique=True)
    requested_amount = models.PositiveIntegerField(_("requested amount"), validators=[MinValueValidator(1)])
    bonus_amount = models.PositiveIntegerField(_("bonus amount"), default=0)
    payable_amount = models.PositiveIntegerField(_("payable amount"))
    payment_card_number = models.CharField(_("payment card number"), max_length=32)
    payment_card_owner = models.CharField(_("payment card owner"), max_length=155)
    receipt_image = models.ImageField(_("receipt image"), upload_to="bot_receipts/", blank=True, null=True)
    receipt_text = models.TextField(_("receipt text"), blank=True)
    receipt_link = models.URLField(_("receipt link"), blank=True)
    transaction_id = models.CharField(_("transaction id"), max_length=120, blank=True)
    admin_note = models.TextField(_("admin note"), blank=True)
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    reviewed_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        related_name="reviewed_bot_payments",
        blank=True,
        null=True,
        verbose_name=_("reviewed by"),
    )
    reviewed_at = models.DateTimeField(_("reviewed at"), blank=True, null=True)
    approved_transaction = models.ForeignKey(
        "WalletTransaction",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="approval_source",
        verbose_name=_("approved transaction"),
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("Bot payment request")
        verbose_name_plural = _("Bot payment requests")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["reference_id"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return f"payment request {self.reference_id} for {self.user_id}"

    @classmethod
    def generate_reference_id(cls) -> str:
        while True:
            reference_id = f"{secrets.randbelow(900000) + 100000}"
            if not cls.objects.filter(reference_id=reference_id).exists():
                return reference_id


class WalletTransaction(models.Model):
    class Kind(models.TextChoices):
        TOP_UP = "top_up", _("Top up")
        ADJUSTMENT = "adjustment", _("Adjustment")
        SPEND = "spend", _("Spend")

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="wallet_transactions",
        verbose_name=_("user"),
    )
    kind = models.CharField(_("kind"), max_length=20, choices=Kind.choices)
    amount = models.PositiveIntegerField(_("amount"))
    previous_balance = models.PositiveIntegerField(_("previous balance"))
    new_balance = models.PositiveIntegerField(_("new balance"))
    reference_code = models.CharField(_("reference code"), max_length=120, blank=True)
    note = models.TextField(_("note"), blank=True)
    request = models.ForeignKey(
        BotPaymentRequest,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="wallet_transactions",
        verbose_name=_("request"),
    )
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="created_wallet_transactions",
        verbose_name=_("created by"),
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Wallet transaction")
        verbose_name_plural = _("Wallet transactions")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["kind", "created_at"]),
        ]

    def __str__(self):
        return f"{self.user_id} {self.kind} {self.amount}"


class BotRequestLog(models.Model):
    endpoint = models.CharField(_("endpoint"), max_length=155)
    method = models.CharField(_("method"), max_length=12)
    ip_address = models.CharField(_("ip address"), max_length=64, blank=True)
    status_code = models.PositiveIntegerField(_("status code"))
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="bot_request_logs",
        verbose_name=_("user"),
    )
    metadata = models.JSONField(_("metadata"), default=dict, blank=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Bot request log")
        verbose_name_plural = _("Bot request logs")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["endpoint", "created_at"]),
        ]

    def __str__(self):
        return f"{self.method} {self.endpoint} {self.status_code}"
