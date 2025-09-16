from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import gettext_lazy as _

from shop.models import Product


class Order(models.Model):
    class OrderStatus(models.TextChoices):
        PENDING_PAYMENT = 'pending_payment', _('Pending Payment')
        PAID = 'paid', _('Paid')
        CANCELLED = 'cancelled', _('Cancelled')
        FAILED = "failed", _("Failed")

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='user_orders',
        verbose_name=_("user"),
    )
    phone_number = models.CharField(_("phone number"), max_length=55)
    name = models.CharField(_("name"), max_length=155)
    telegram_id = models.CharField(_("telegram_id"), max_length=55, blank=True)
    final_price = models.PositiveIntegerField(_("final_price"))
    status = models.CharField(_("status"), max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING_PAYMENT)
    created_at = models.DateTimeField(_("created_at"),auto_now_add=True)
    updated_at = models.DateTimeField(_("updated_at"), auto_now=True)

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")

    def __str__(self):
        return f"order: {self.id} for {self.name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="+")
    item_price = models.CharField(max_length=155)
    is_completed = models.BooleanField(default=False)
    item_final_price = models.CharField(max_length=155)

    class Meta:
        verbose_name = _("Order Items")
        verbose_name_plural = _("Items")

    def save(
        self,
        *args,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        self.item_price = self.product.price
        self.item_final_price = self.product.get_final_price()
        return super().save()

    def __str__(self):
        return f"item:{self.id}"