from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from django.utils.text import gettext_lazy as _
import random


class CustomUser(AbstractUser):
    phone = models.CharField(_("phone"), max_length=32, unique=True, blank=True, null=True)
    full_name = models.CharField(_("full name"), max_length=150, blank=True)
    telegram_id = models.CharField(_("telegram id"), max_length=55, blank=True)
    wallet_balance = models.PositiveIntegerField(_("wallet balance"), default=0)

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")


class SiteSettings(models.Model):
    site_name1 = models.CharField(_("site name1"), max_length=55)
    site_name2 = models.CharField(_("site name2"), max_length=55)
    site_logo = models.ImageField(_("site logo"), upload_to='logo/')
    payment_card = models.CharField(_("payment card number"), max_length=155)
    payment_card_name = models.CharField(_("payment card owner name"), max_length=155)
    up_time = models.CharField(_("servers uptime"), max_length=55)
    countries_count = models.CharField(_("countries count"), max_length=55)
    servers_count = models.CharField(_("servers count"), max_length=55)
    footer_text = models.CharField(_("footer text"), max_length=155)

    users_count_for_about_us = models.CharField(_("users_count_for_about_us"), max_length=55)
    established_year_for_about_us = models.CharField(_("established_year_for_about_us"), max_length=55)
    feature1_for_about_us = models.CharField(_("feature1_for_about_us"), max_length=55)
    feature2_for_about_us = models.CharField(_("feature2_for_about_us"), max_length=55)
    feature3_for_about_us = models.CharField(_("feature3_for_about_us"), max_length=55)
    feature4_for_about_us = models.CharField(_("feature4_for_about_us"), max_length=55)

    telegram_support_id_link = models.URLField(_("telegram_support_id_link"), )
    telegram_Channel_id_link = models.URLField(_("telegram_Channel_id_link"), )
    telegram_bot_id_link = models.URLField(_("telegram_bot_id_link"), )

    def __str__(self):
        return f"settings of {self.site_name1} {self.site_name2}"

    class Meta:
        verbose_name = _("SiteSetting")
        verbose_name_plural = _("SiteSettings")


class FrequentlyAskedQuestions(models.Model):
    question = models.CharField(_("question"), max_length=255)

    class Meta:
        verbose_name = _("FrequentlyAskedQuestion")
        verbose_name_plural = _("FrequentlyAskedQuestions")


class Answer(models.Model):
    question = models.ForeignKey(
        FrequentlyAskedQuestions,
        on_delete=models.PROTECT,
        related_name='answers',
        verbose_name=_("question")
    )
    answer = models.CharField(_("answer"),max_length=255)
