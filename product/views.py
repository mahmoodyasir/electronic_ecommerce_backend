from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import generics

from product.models import Product
from .serializers import ProductSerializer
from asgiref.sync import sync_to_async
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAdminUser
from .tasks import create_product_task, delete_product_task, get_all_products_task, get_single_product_task


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
    
    def create(self, request):
        self.permission_classes = [IsAdminUser]  
        self.check_permissions(request)  

        tasks = create_product_task.delay(request.data)

        try:   
            result = tasks.get(timeout=10)
            
            print(result)

            if result.get('success') is False:
                raise Exception(result.get('error'))

            return Response({
                "message": "Product creation complete.",
                "product_data": result.get('product_data')
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def list(self, request):

        skip = int(request.query_params.get('skip', 1))
        limit = int(request.query_params.get('limit', 10))
        task = get_all_products_task.delay(skip, limit) 
        result = task.get(timeout=10)
        return Response(result, status=status.HTTP_200_OK)


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