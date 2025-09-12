from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=155)
    time_limit = models.CharField(max_length=155)
    traffic_limit = models.CharField(max_length=155)
    device_connections_limit = models.CharField(max_length=155)
    feature1 = models.CharField(max_length=155)
    feature2 = models.CharField(max_length=155)
    feature3 = models.CharField(max_length=155)
    is_special = models.BooleanField(default=False)

    def __str__(self):
        return self.name



