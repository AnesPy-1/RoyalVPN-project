from django.db import models
from django.contrib.auth import get_user_model

from shop.models import Product


class Cart(models.Model):
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='user_carts',
        null=True,
        blank=True,
    )
    session_key = models.CharField(max_length=55, blank=True)

    def __str__(self):
        return f"cart: {self.id}"

    def get_cart_old_total(self):
        return sum([item.product.price for item in self.items.select_related('product')])

    def get_cart_final_price(self):
        return sum([item.product.get_final_price() for item in self.items.select_related('product')])

    def cart_total_discount(self):
        return int(self.get_cart_old_total() - self.get_cart_final_price())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"item: {self.id}"
