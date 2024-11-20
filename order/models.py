from datetime import datetime
import string
from django.db import models
from django.conf import settings
from product.models import Product
import random


class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('on_the_way', 'On The Way'),
        ('completed', 'Completed'),
        ('shipped', 'Shipped'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order_ID = models.CharField(max_length=255, null=True, blank=True)
    shipping_address = models.CharField(max_length=255, blank=True, null=True)
    payment_complete = models.BooleanField(default=False)
    payment_type = models.CharField(max_length=200, default="cash")
    total = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.order_ID} by {self.user.email}"
    
    def save(self, *args, **kwargs):
        if not self.order_ID:
            current_time = datetime.now().strftime('%Y%m%d%H%M%S')
            random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) 
            self.order_ID = f"{random_suffix}-{current_time}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    sub_total = models.DecimalField(max_digits=15, decimal_places=2)
    
    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"
    
    def save(self, *args, **kwargs):
        # Calculate the subtotal based on the product price and quantity
        price = self.product.discount_price if self.product.discount_price and self.product.discount_price > 0 else self.product.price
        self.sub_total = price * self.quantity
        
        # Update inventory
        inventory = self.product.inventory_product
        
        if inventory.quantity >= self.quantity:
            inventory.quantity -= self.quantity
            inventory.save()
        else:
            raise ValueError(f"Not enough stock for {self.product.name}. Available: {inventory.quantity}")
        
        super().save(*args, **kwargs)



    
    
class OnlinePayment(models.Model):
    order = models.ForeignKey(Order, related_name="online_payment", on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=255, null=True, blank=True)
    card_brand = models.CharField(max_length=255, null=True, blank=True)
    card_issuer = models.CharField(max_length=255, null=True, blank=True)
    total_paid = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=150, null=True, blank=True)
    
    def __str__(self):
        return f"T.ID: {self.transaction_id}, Medium: {self.card_issuer}"