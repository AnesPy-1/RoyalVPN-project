from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Users must have a phone number")
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
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
    username = models.CharField(max_length=150, null=True, blank=True)
    phone = models.CharField(max_length=32, unique=True)
    email = models.EmailField(blank=True, null=True)
    full_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    objects = UserManager()


class SiteSettings(models.Model):
    site_name1 = models.CharField(max_length=55)
    site_name2 = models.CharField(max_length=55)
    site_logo = models.URLField()
    up_time = models.CharField(max_length=55)
    countries_count = models.CharField(max_length=55)
    servers_count = models.CharField(max_length=55)
    footer_text = models.CharField(max_length=155)

    users_count_for_about_us = models.CharField(max_length=55)
    established_year_for_about_us = models.CharField(max_length=55)
    feature1_for_about_us = models.CharField(max_length=55)
    feature2_for_about_us = models.CharField(max_length=55)
    feature3_for_about_us = models.CharField(max_length=55)
    feature4_for_about_us = models.CharField(max_length=55)


class FrequentlyAskedQuestions(models.Model):
    question = models.CharField(max_length=55)

class Answer(models.Model):
    question = models.ForeignKey(FrequentlyAskedQuestions, on_delete=models.PROTECT, related_name='answers')
    answer = models.CharField(max_length=55)


