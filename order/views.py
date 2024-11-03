from django.shortcuts import render
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from .serializers import CreateOrderSerializer, OrderSerializer
from .models import Order, OrderItem

class OrderViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        try:   
            
            serializer = CreateOrderSerializer(data=request.data, context={'request': request})
            
            if serializer.is_valid():
                order = serializer.save()

                return Response({
                    'status': 'Order created successfully',
                    'order_id': order.order_ID,
                    'total': order.total,
                    'shipping_address': order.shipping_address,
                    'payment_type': order.payment_type,
                }, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    
    def list(self, request):
        # self.permission_classes = [IsAdminUser]
        # self.check_permissions(request)
        
        try:
            # all_orders = Order.objects.prefetch_related('items__product').all()
            all_orders = Order.objects.prefetch_related('items__product').filter(user=request.user)
            serializer = OrderSerializer(all_orders, many=True)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
