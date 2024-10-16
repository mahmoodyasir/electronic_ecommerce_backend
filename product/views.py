from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import generics
from .serializers import ProductSerializer
from asgiref.sync import sync_to_async
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from .tasks import create_product_task


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
                "product_data": result.get('product')
                
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)