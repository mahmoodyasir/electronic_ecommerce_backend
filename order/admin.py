from django.contrib import admin
from .models import *


class OrderAdmin(admin.ModelAdmin):
    search_fields = ["id", "order_ID"]
    list_display = ["id", "order_ID", "shipping_address", "payment_complete", "payment_type", "total", "status", "created_at", "updated_at"]
    list_per_page = 10
    
    
class OrderItemAdmin(admin.ModelAdmin):
    search_fields = ["id", "order"]
    list_display = ["id", "order", "product", "quantity", "sub_total"]
    list_per_page = 10
    
    
class OnlinePaymentAdmin(admin.ModelAdmin):
    search_fields = ["id", "transaction_id"]
    list_display = ["id", "order", "transaction_id", "card_brand", "card_issuer", "total_paid", "currency"]
    list_per_page = 10
    
    
    
admin.site.register(Order, OrderAdmin) 
admin.site.register(OrderItem, OrderItemAdmin) 
admin.site.register(OnlinePayment, OnlinePaymentAdmin) 
    