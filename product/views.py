from datetime import datetime
import uuid
from django.shortcuts import render
import json
import urllib.parse
from adrf.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import generics
from product.models import Product, KeyFeature, Specification, Category
from utils import utils
from .serializers import ProductSerializer, KeyFeatureSerializer, SpecificationSerializer, CategorySerializer
from asgiref.sync import sync_to_async
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAdminUser
from .tasks import create_product_task, delete_image_from_s3_task, delete_product_task, get_all_products_task, get_single_product_task, upload_image_to_s3_task
from django.conf import settings
import boto3
import mimetypes
from django.core.files.storage import default_storage

class ProductCreateView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        
        tasks = create_product_task.delay(request.data)
        
        try:   
            result = tasks.get(timeout=10)
            
            if result.get('success') == False:
                raise Exception(result.get('errors'))
            
            return Response({
                "message": "Product creation complete.",
                "product_data": result.get('product_data')
                
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

# class ProductListView(APIView):
#     def get(self, request):
    
#         skip = int(request.query_params.get('skip', 1))
#         limit = int(request.query_params.get('limit', 10))
#         task = get_all_products_task.delay(skip, limit) 
#         result = task.get(timeout=10)
#         return Response(result, status=status.HTTP_200_OK)
    
    
# class ProductDetailView(APIView):
#     def get(self, request, id):
#         task = get_single_product_task.delay(id) 
        
#         result = task.get(timeout=10)  
        
#         if 'error' in result:
#             return Response(result, status=status.HTTP_404_NOT_FOUND)

#         return Response(result, status=status.HTTP_200_OK)
    
    
    
    
class ProductViewSet(viewsets.ViewSet):
    parser_classes = (MultiPartParser, FormParser) 
    
    def create(self, request):
        self.permission_classes = [IsAdminUser]  
        self.check_permissions(request)  
        
        try:   
            key_features_data = json.loads(request.data.get('key_features', '[]'))
            specifications_data = json.loads(request.data.get('specifications', '[]'))
            inventory_product_data = json.loads(request.data.get('inventory_product', '{}'))
            

            images = request.FILES.getlist('images')  # Get all uploaded images
            image_urls = []

            
            for image in images:
                file_type = mimetypes.guess_type(image.name)[0].split('/')[-1]
                unique_filename = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_type}"
                sanitized_filename = urllib.parse.quote(image.name.replace(" ", "_"))
                temp_file_path = default_storage.save(f'static/{unique_filename}', image)
                upload_image_to_s3_task.delay(temp_file_path, unique_filename)
                
                image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/products/{unique_filename}"
                image_urls.append(image_url)


            
            serializer_data = {
                'name': request.data.get('name', None),
                'price': request.data.get('price', None),
                'discount_price': request.data.get('discount_price', None),
                'brand': request.data.get('brand', None),
                'category': request.data.get('category', None),
                'description': request.data.get('description', None),
                'key_features': key_features_data,
                'specifications': specifications_data,
                'inventory_product': inventory_product_data,
                'image_urls': image_urls,
            }
            
 
            serializer = ProductSerializer(data=serializer_data)
            
            if serializer.is_valid():
                product = serializer.save()
                product_data = ProductSerializer(product).data

                return Response({
                    "message": "Product creation complete.",
                    "product_data": product_data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
    def update(self, request, pk=None):
        self.permission_classes = [IsAdminUser]
        self.check_permissions(request)

        try:
            product = Product.objects.get(pk=pk)

            key_features_data = json.loads(request.data.get('key_features', '[]'))
            specifications_data = json.loads(request.data.get('specifications', '[]'))
            inventory_product_data = json.loads(request.data.get('inventory_product', '{}'))

            updated_image_urls = json.loads(request.data.get('image_urls', '[]'))
            existing_image_urls = list(product.image_urls)  
            
            images_to_delete = set(existing_image_urls) - set(updated_image_urls)
            new_images = request.FILES.getlist('images')  

            # Delete old images using Celery
            for image_url in images_to_delete:
                delete_image_from_s3_task.delay(image_url)
            
            # Upload new images using Celery and collect new URLs
            new_image_urls = []
            for image in new_images:
                file_type = mimetypes.guess_type(image.name)[0].split('/')[-1]
                unique_filename = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_type}"
                sanitized_filename = urllib.parse.quote(image.name.replace(" ", "_"))
                temp_file_path = default_storage.save(f'static/{unique_filename}', image)
                upload_image_to_s3_task.delay(temp_file_path, unique_filename)

                new_image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/products/{unique_filename}"
                new_image_urls.append(new_image_url)
            
            # Combining existing URLs with new ones
            updated_image_urls.extend(new_image_urls)
            
            serializer_data = {
                'name': request.data.get('name', None),
                'price': request.data.get('price', None),
                'discount_price': request.data.get('discount_price', None),
                'brand': request.data.get('brand', None),
                'category': request.data.get('category', None),
                'description': request.data.get('description', None),
                'key_features': key_features_data,
                'specifications': specifications_data,
                'inventory_product': inventory_product_data,
                'image_urls': updated_image_urls,
            }

            serializer = ProductSerializer(product, data=serializer_data, partial=True)
            if serializer.is_valid():
                product = serializer.save()
                return Response(ProductSerializer(product).data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Product.DoesNotExist:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def list(self, request):

        skip = int(request.query_params.get('skip', 1))
        limit = int(request.query_params.get('limit', 10))
        task = get_all_products_task.delay(skip, limit) 
        result = task.get(timeout=10)
        
        # response = {
        #     "page": skip,
        #     "limit": limit,
        #     "total": result.total
        # }
        return Response({
            "page": skip,
            "limit": limit,
            "total": result['total'],
            "data": result['data']
        }, status=status.HTTP_200_OK)


    def retrieve(self, request, pk=None):

        task = get_single_product_task.delay(pk) 
        result = task.get(timeout=10)  

        if 'error' in result:
            return Response(result, status=status.HTTP_404_NOT_FOUND)

        return Response(result, status=status.HTTP_200_OK)
    
    
    def destroy(self, request, pk=None):
        self.permission_classes = [IsAdminUser]
        self.check_permissions(request)

        task = delete_product_task.delay(pk)
        
        try:
            result = task.get(timeout=10)
            
            if result.get('success') is False:
                raise Exception(result.get('errors'))

            return Response({
                "message": "Product deleted successfully.",
                "product_data": result.get('product_data')
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
        
class UpdateProductImagesView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAdminUser]  

    def put(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
            
            new_images = request.FILES.getlist('images')  
        
            new_image_urls = []
            for image in new_images:
                file_type = mimetypes.guess_type(image.name)[0].split('/')[-1]
                unique_filename = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_type}"
                sanitized_filename = urllib.parse.quote(image.name.replace(" ", "_"))
                temp_file_path = default_storage.save(f'static/{unique_filename}', image)
                upload_image_to_s3_task.delay(temp_file_path, unique_filename)

                new_image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/products/{unique_filename}"
                new_image_urls.append(new_image_url)

            product.image_urls = new_image_urls
            product.save()

            return Response({
                "message": "Product images updated successfully.",
                "image_urls": product.image_urls
            }, status=status.HTTP_200_OK)

        except Product.DoesNotExist:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
        
class KeyFeatureView(APIView):
    
    async def get(self, request):
        
        category_name = request.query_params.get("category", None)
        
        all_category = await sync_to_async(list)(Category.objects.all())
        
        if category_name:
            feature = await sync_to_async(list)(KeyFeature.objects.filter(product__category__name = category_name))
        else:
            feature = await sync_to_async(list)(KeyFeature.objects.all())
            
        serializer_keyfeature = KeyFeatureSerializer(feature, many=True)
        serializer_category = CategorySerializer(all_category, many=True)
        
        all_data = serializer_keyfeature.data
        
        dict = {}
        
        for item in all_data:
            key = item["name"]
            value = item["value"]
            
            if key in dict:
                dict[key].update(value)
            else:
                dict[key] = set(value)
                
        
        return Response({
            "success": True,
            "message": "Feature and Category Fetched",
            "data": {
                "category": serializer_category.data,
                "feature": dict
            }
        })
    
    
class SpecificationView(APIView):
    
    async def get(self, request):
        
        feature = await sync_to_async(list)(Specification.objects.all())
        
        serializer = SpecificationSerializer(feature, many=True)
        
        all_data = serializer.data
        
        dict = {}
        
        for item in all_data:
            category = str(item["category"]).lower()
            name = str(item["name"]).lower()
            value = item["value"]
            
            if category not in dict:
                dict[category] = {}
            
            if name not in dict[category]:
                dict[category][name] = set()
            
            for val in item["value"]:
                dict[category][name].add(val)
                
        
        return Response({"data": dict})


class ProductFilterView(APIView):
    async def post(self, request):
        try:

            name_filter = request.data.get('name', None)
            category_filter = request.data.get('category', None)
            key_features = request.data.get('key_features', [])
            min_price = request.data.get('min_price', None)
            max_price = request.data.get('max_price', None)

            skip = int(request.query_params.get('skip', 1))
            limit = int(request.query_params.get('limit', 10))

            task = get_all_products_task.delay(skip, limit, name_filter, category_filter, key_features, min_price, max_price)
            
            result = task.get(timeout=10)

            # return Response({
            #     "page": skip,
            #     "limit": limit,
            #     "total": result['total'],
            #     "data": result['data']
            # }, status=status.HTTP_200_OK)
            
            return utils.create_response(
                success=True,
                message="All Filtered Products Fetched",
                status_code=status.HTTP_200_OK,
                page=skip,
                page_size=limit,
                total=result['total'],
                total_page=result['total_page'],
                data=result['data'] 
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)