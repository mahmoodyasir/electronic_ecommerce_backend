from django.contrib import admin
from .models import *


class InventoryAdmin(admin.ModelAdmin):
    search_fields = ["id", "product"]
    list_display = ["id", "product", "quantity", "restock_alert", "last_restocked"]
    list_per_page = 10


admin.site.register(Inventory, InventoryAdmin)