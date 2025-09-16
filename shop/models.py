from django.db import models
from django.utils.translation import gettext_lazy as _


class Discount(models.Model):
    value = models.PositiveIntegerField(_("Discount value"))

    def __str__(self):
        return f"{self.value}%"

    class Meta:
        verbose_name = _("Discount")
        verbose_name_plural = _("Discounts")


class Product(models.Model):
    name = models.CharField(_("Name"), max_length=155)
    time_limit = models.CharField(_("Time limit"), max_length=155, help_text=_("unlimited: 0"))
    time_limit_NUM = models.IntegerField(_("Time limit (numeric)"), help_text=_("unlimited: 0"))
    traffic_limit = models.CharField(_("Traffic limit"), max_length=155, help_text=_("unlimited: 0"))
    traffic_limit_NUM = models.DecimalField(_("Traffic limit (numeric)"), max_digits=5, decimal_places=2, null=True, blank=True)

    device_connections_limit = models.CharField(_("Device connections limit"), max_length=155, help_text=_("unlimited: 0"))
    price = models.PositiveIntegerField(_("Price"))
    discount = models.ForeignKey(
        Discount,
        on_delete=models.PROTECT,
        related_name='discount_products',
        null=True,
        blank=True,
        verbose_name=_("Discount"),
    )
    feature1 = models.CharField(_("Feature 1"), max_length=155, blank=True)
    feature2 = models.CharField(_("Feature 2"), max_length=155, blank=True)
    feature3 = models.CharField(_("Feature 3"), max_length=155, blank=True)
    is_special = models.BooleanField(_("Is special"), default=False)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    def get_final_price(self):
        if self.discount:
            return max(self.price * (1 - self.discount.value / 100), 0)
        return self.price

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")


class Comment(models.Model):
    display_name = models.CharField(_("Display name"), max_length=55)
    user_profile = models.ImageField(_("User profile image"), upload_to='comments/')
    user_city = models.CharField(_("User city"), max_length=55)
    text = models.TextField(_("Comment text"))
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = _("Comment")
        verbose_name_plural = _("Comments")
