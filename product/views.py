from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import generics
from .serializers import ProductSerializer
from asgiref.sync import sync_to_async
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser


class ProductCreateView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = ProductSerializer(data=request.data)

        if serializer.is_valid():
            product = serializer.save()
            product_data = ProductSerializer(product).data
            return Response(product_data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

