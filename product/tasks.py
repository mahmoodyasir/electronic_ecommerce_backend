import boto3
from celery import shared_task
from django.conf import settings
import urllib.parse
from .models import Product
from .serializers import ProductSerializer
from django.core.exceptions import ValidationError
import mimetypes
from django.core.files.storage import default_storage

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
    
    
    
    
@shared_task
def upload_image_to_s3_task(temp_file_path, file_name):
    try:
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )

        # Construct the destination file path in S3
        s3_file_path = f"products/{file_name}"

        # Upload the file from the temporary location to S3
        with default_storage.open(temp_file_path, 'rb') as file_data:
            s3_client.upload_fileobj(
                file_data,
                settings.AWS_STORAGE_BUCKET_NAME,
                s3_file_path,
                ExtraArgs={
                    'ACL': 'public-read',
                    'ContentType': mimetypes.guess_type(file_name)[0] or 'application/octet-stream',
                    'ContentDisposition': 'inline'
                }
            )
            
        image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{s3_file_path}"

        default_storage.delete(temp_file_path)

        return image_url

    except Exception as e:
        return str(e)