from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import gettext_lazy as _

from orders.models import Order
from subs.models import Subscriptions

class Payment(models.Model):
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        verbose_name=_("order"),

    )
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='user_payments',
        verbose_name=_("user"),
    )
    payment_picture = models.ImageField(_("payment picture"), upload_to='payment/', blank=True, null=True)
    total_price = models.PositiveIntegerField(_("total price"))
    subs = models.ManyToManyField(
        Subscriptions,
        related_name='payments',
        blank=True,
        verbose_name=_("subs"),
    )
    is_used = models.BooleanField(_("is used"), default=False)

    created_at = models.DateTimeField(_("created_at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")

    def __str__(self):
        return f"user {self.user.full_name} paid {self.total_price} at {self.created_at}"