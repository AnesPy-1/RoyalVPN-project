from django.db import models
from django.contrib.auth import get_user_model

from orders.models import Order
from subs.models import Subscriptions

class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='user_payments')
    payment_picture = models.ImageField(upload_to='payment/')
    total_price = models.PositiveIntegerField()
    subs = models.ManyToManyField(Subscriptions, related_name='payments', blank=True)
    is_used = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"user {self.user.full_name} paid {self.total_price} at {self.created_at}"