from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone


class SubscriptionLinks(models.Model):
    class TypeChoices(models.TextChoices):
        TEST = 'test', "test"
        SUB = 'sub', 'Subscription'

    plan_type = models.CharField(max_length=10, choices=TypeChoices.choices, default=TypeChoices.SUB)
    sub_link = models.CharField(max_length=255)
    day_limit = models.IntegerField(null=True, blank=True)
    traffic_limit = models.IntegerField(null=True, blank=True)
    price = models.PositiveIntegerField()
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return self.sub_link

class Subscriptions(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, related_name='user_subscriptions')
    sub = models.ForeignKey(SubscriptionLinks, on_delete=models.PROTECT, related_name='+')
    is_test = models.BooleanField(default=False)
    expire_date = models.DateTimeField()

    def save(
        self,
        *args,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        if self.sub.day_limit:
            self.expire_date = timezone.now() - timezone.timedelta(days=self.sub.day_limit)
        return super().save(*args)

    def __str__(self):
        return self.user
