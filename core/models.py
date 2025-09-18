from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from django.utils.text import gettext_lazy as _
import random


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Users must have a phone number")
        user = self.model(phone=phone, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(phone, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(_("username"), max_length=150, null=True, blank=True)
    phone = models.CharField(_("phone"), max_length=32, unique=True)
    email = models.EmailField(_("email"), blank=True, null=True)
    full_name = models.CharField(_("full name"), max_length=150, blank=True)
    is_active = models.BooleanField(_("is active"), default=True)
    is_staff = models.BooleanField(_("is staff"), default=False)
    is_phone_verified = models.BooleanField(_("is phone verified"), default=False)
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    telegram_id = models.CharField(_("telegram id"), max_length=55, blank=True)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    objects = UserManager()

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


class OTP(models.Model):
    phone = models.CharField(max_length=15)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)


    @staticmethod
    def generate_code():
        return str(random.randint(100000, 999999))

    def is_valid(self):
        return (timezone.now() - self.created_at).seconds < 120 and not self.is_used
