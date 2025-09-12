from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=155)
    time_limit = models.CharField(max_length=155, help_text="unlimited: 0")
    traffic_limit = models.CharField(max_length=155, help_text="unlimited: 0")
    device_connections_limit = models.CharField(max_length=155, help_text="unlimited: 0")
    feature1 = models.CharField(max_length=155, blank=True)
    feature2 = models.CharField(max_length=155, blank=True)
    feature3 = models.CharField(max_length=155, blank=True)
    is_special = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Comment(models.Model):
    display_name = models.CharField(max_length=55)
    user_profile = models.ImageField(upload_to='comments/')
    user_city = models.CharField(max_length=55)
    text = models.TextField()

    def __str__(self):
        return self.text
