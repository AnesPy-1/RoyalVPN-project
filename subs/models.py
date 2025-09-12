from django.db import models

class Subscription(models.Model):
    class TypeChoices(models.TextChoices):
        TEST = 'test', "test"
        SUB = 'sub', 'Subscription'

    plan_type = models.CharField(max_length=10, choices=TypeChoices.choices)
    name = models.CharField(max_length=155)
    sub_link = models.CharField(max_length=255)
    day_limit = models.IntegerField()
    traffic_limit = models.IntegerField()
    price = models.PositiveIntegerField()
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return self.name


