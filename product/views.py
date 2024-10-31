from django.shortcuts import render
import json
import urllib.parse
from adrf.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import generics
from product.models import Product, KeyFeature, Specification, Category
from .serializers import ProductSerializer, KeyFeatureSerializer, SpecificationSerializer
from asgiref.sync import sync_to_async
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAdminUser
from .tasks import create_product_task, delete_product_task, get_all_products_task, get_single_product_task, upload_image_to_s3_task
from django.conf import settings
import boto3
import mimetypes
from django.core.files.storage import default_storage

# class ProductCreateView(APIView):
#     permission_classes = [IsAdminUser]

#     def post(self, request):
        
#         tasks = create_product_task.delay(request.data)
        
#         try:   
#             result = tasks.get(timeout=10)
            
#             if result.get('success') == False:
#                 raise Exception(result.get('errors'))
            
#             return Response({
#                 "message": "Product creation complete.",
#                 "product_data": result.get('product')
                
#             }, status=status.HTTP_201_CREATED)
#         except Exception as e:
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

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
                sanitized_filename = urllib.parse.quote(image.name.replace(" ", "_"))
                temp_file_path = default_storage.save(f'static/{sanitized_filename}', image)
                upload_image_to_s3_task.delay(temp_file_path, sanitized_filename)
                
                image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/products/{sanitized_filename}"
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
            
            print(result)
            
            if result.get('success') is False:
                raise Exception(result.get('errors'))

            return Response({
                "message": "Product deleted successfully.",
                "product_data": result.get('product_data')
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
        
class KeyFeatureView(APIView):
    
    async def get(self, request):
        
        feature = await sync_to_async(list)(KeyFeature.objects.all())
        
        serializer = KeyFeatureSerializer(feature, many=True)
        
        all_data = serializer.data
        
        dict = {}
        
        for item in all_data:
            key = item["name"].lower()
            value = item["value"]
            
            if key in dict:
                dict[key].update(value)
            else:
                dict[key] = set(value)
                
        
        return Response({"data": dict})
    
    
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