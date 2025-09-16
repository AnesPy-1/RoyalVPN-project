from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class SubscriptionLinks(models.Model):
    class TypeChoices(models.TextChoices):
        TEST = 'test', _("Test")
        SUB = 'sub', _("Subscription")

    plan_type = models.CharField(
        _("Plan type"),
        max_length=10,
        choices=TypeChoices.choices,
        default=TypeChoices.SUB,
    )
    sub_link = models.CharField(_("Subscription link"), max_length=255)
    day_limit = models.IntegerField(_("Day limit"), help_text=_("Unlimited=0"))
    traffic_limit = models.IntegerField(_("Traffic limit"))
    is_test = models.BooleanField(_("Is test"), default=False)
    is_used = models.BooleanField(_("Is used"), default=False)

    def __str__(self):
        return self.sub_link

    class Meta:
        verbose_name = _("Subscription link")
        verbose_name_plural = _("Subscription links")


class Subscriptions(models.Model):
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        related_name='user_subscriptions',
        verbose_name=_("User"),
    )
    sub = models.ForeignKey(
        SubscriptionLinks,
        on_delete=models.PROTECT,
        related_name='+',
        verbose_name=_("Subscription link"),
    )
    is_test = models.BooleanField(_("Is test"), default=False)
    expire_date = models.DateTimeField(_("Expire date"), null=True, blank=True)
    is_active = models.BooleanField(_("Is active"), default=True)

    def save(
        self,
        *args,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        if self.sub.day_limit:
            self.expire_date = timezone.now() + timezone.timedelta(days=self.sub.day_limit)
        return super().save(*args)

    class Meta:
        verbose_name = _("Subscription")
        verbose_name_plural = _("Subscriptions")
