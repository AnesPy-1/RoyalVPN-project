from django.db import models
from django.contrib.auth import get_user_model

from shop.models import Product


class Order(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='user_orders')
    phone_number = models.CharField(max_length=55)
    name = models.CharField(max_length=155)

    def __str__(self):
        return f"order: {self.id} for {self.name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="+")
    item_price = models.CharField(max_length=155)
    item_final_price = models.CharField(max_length=155)

    def save(
        self,
        *args,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        self.item_price = self.product.price
        self.item_final_price = self.product.get_final_price()

    def __str__(self):
        return self.product