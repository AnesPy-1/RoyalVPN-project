from django.db import models
from django.contrib.auth import get_user_model

from orders.models import Order


class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='user_payments')
    payment_picture = models.ImageField(upload_to='payment/')
    total_price = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"user {self.user.name} paid {self.total_price} at {self.created_at}"