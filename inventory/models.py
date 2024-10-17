from django.db import models
from asgiref.sync import sync_to_async
from django.utils import timezone
from product.models import Product


class Inventory(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="inventory_product")
    quantity = models.IntegerField()
    restock_alert = models.IntegerField()
    last_restocked = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.product.name}"
        