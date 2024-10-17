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


@shared_task
def get_all_products_task(page=1, page_size=10):
    offset = (page - 1) * page_size
    products = Product.objects.select_related('inventory_product').all()[offset:offset + page_size] 
    
    total_product = Product.objects.count()
    
    serialized_products = ProductSerializer(products, many=True).data
    
    response = {
        "total": total_product,
        "data": serialized_products
    }
    
    return response


@shared_task
def get_single_product_task(product_id):
    try:
        product = Product.objects.get(id=product_id)
        return ProductSerializer(product).data
    except Product.DoesNotExist:
        return {"error": "Product not found"}
    
    
    
@shared_task
def delete_product_task(product_id):
    try:
        product = Product.objects.get(id=product_id)
        product_data = ProductSerializer(product).data
        product.delete()
        
        return {'success': True, "product_data": product_data}
    except Product.DoesNotExist:
        return {'success': False, 'errors': 'Product not found.'}
    except Exception as e:
        return {'success': False, 'errors': str(e)}