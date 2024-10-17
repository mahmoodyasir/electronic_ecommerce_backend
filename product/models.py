from django.db import models
from django.contrib.postgres.fields import ArrayField
from datetime import datetime
import uuid

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
    
def generate_product_code():
    now = datetime.now()
    month_year = now.strftime("%b%Y")  # e.g., 'Oct2024'
    unique_id = str(uuid.uuid4())[:8]
    product_code = f"{unique_id}{month_year}"
    return product_code


class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=100, decimal_places=2)
    discount_price = models.DecimalField(max_digits=100, decimal_places=2, blank=True, null=True)
    product_code = models.CharField(max_length=100, unique=True)
    brand = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')  
    description = models.TextField()
    image_urls = ArrayField(models.URLField(max_length=200), blank=True, default=list) 

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.product_code:
            self.product_code = generate_product_code()
        super().save(*args, **kwargs)
        

class KeyFeature(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='key_features')
    name = models.CharField(max_length=100)  
    value = ArrayField(models.CharField(max_length=255))  

    def __str__(self):
        return f"{self.name}: {', '.join(self.value)}"

class Specification(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specifications')
    category = models.CharField(max_length=100) 
    name = models.CharField(max_length=100)    
    value = ArrayField(models.CharField(max_length=255)) 

    def __str__(self):
        return f"{self.category} - {self.name}: {', '.join(self.value)}"
