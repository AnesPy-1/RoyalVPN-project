from django.db import models

class Discount(models.Model):
    value = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.value}%"


class Product(models.Model):
    name = models.CharField(max_length=155)
    time_limit = models.CharField(max_length=155, help_text="unlimited: 0")
    time_limit_NUM = models.IntegerField(help_text="unlimited: 0")
    traffic_limit = models.CharField(max_length=155, help_text="unlimited: 0")
    traffic_limit_NUM = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    device_connections_limit = models.CharField(max_length=155, help_text="unlimited: 0")
    price = models.PositiveIntegerField()
    discount = models.ForeignKey(
        Discount,
        on_delete=models.PROTECT,
        related_name='discount_products',
        null=True,
        blank=True,
    )
    feature1 = models.CharField(max_length=155, blank=True)
    feature2 = models.CharField(max_length=155, blank=True)
    feature3 = models.CharField(max_length=155, blank=True)
    is_special = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_final_price(self):
        if self.discount:
            return max(self.price * (1 - self.discount.value / 100), 0)
        return self.price

    def __str__(self):
        return self.name

class Comment(models.Model):
    display_name = models.CharField(max_length=55)
    user_profile = models.ImageField(upload_to='comments/')
    user_city = models.CharField(max_length=55)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.text
