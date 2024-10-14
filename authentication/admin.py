from django.contrib import admin
from .models import *


class CustomUserAdmin(admin.ModelAdmin):
    search_fields = ['id', 'email', 'phone_number']
    list_display = ['username','email', 'first_name', 'last_name', 'phone_number', 'address', 'image_url']
    list_per_page = 10
    
    
admin.site.register(CustomUser, CustomUserAdmin)
