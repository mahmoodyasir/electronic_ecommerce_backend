from celery import shared_task
from .models import Product
from .serializers import ProductSerializer
from django.core.exceptions import ValidationError

@shared_task
def create_product_task(product_data):
    try:
        serializer = ProductSerializer(data=product_data)
        if serializer.is_valid():
            product = serializer.save()
            product_data = ProductSerializer(product).data
            return {"success": True, "product_data": product_data}
        else:
            return {"success": False, "error": serializer.errors}
    except Exception as e:
        return {"success": False, "error": str(e)}
