from django.contrib import admin
from .models import *

class CategoryAdmin(admin.ModelAdmin):
    search_fields = ["id", "name"]
    list_display = ["id", "name"]
    list_per_page = 10
    
    
class KeyFeatureAdmin(admin.ModelAdmin):
    search_fields = ["id", "name"]
    list_display = ["id", "product", "name", "value"]
    list_per_page = 10
    
    
class SpecificationAdmin(admin.ModelAdmin):
    search_fields = ["id", "category"]
    list_display = ["id", "product", "category", "name", "value"]
    list_per_page = 10
    
    
class ProductAdmin(admin.ModelAdmin):
    search_fields = ["id", "name"]
    list_display = ['id', 'name', 'price', 'discount_price', 'product_code', 
                  'brand', 'category', 'image_urls', 'description']
    list_per_page = 10
    
    
    

admin.site.register(Category, CategoryAdmin)
admin.site.register(KeyFeature, KeyFeatureAdmin)
admin.site.register(Specification, SpecificationAdmin)
admin.site.register(Product, ProductAdmin)