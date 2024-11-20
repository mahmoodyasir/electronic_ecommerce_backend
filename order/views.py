from decimal import Decimal
import json
import uuid
from django.conf import settings
from django.shortcuts import redirect, render
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from product.models import Product
from utils.sslcommerz import SSLCSession
from .serializers import CreateOrderSerializer, OrderSerializer
from .models import Order, OrderItem
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from django.urls import reverse
from django.http import HttpResponseRedirect

def handleOnlineOrder(request, orderInfo, userInfo, orderId):
    
    gross_total = 0
    total_quantity = 0
    
    for product_id, quantity in orderInfo['products'].items():
        try:
            product = Product.objects.get(id=product_id, isActive=True)
            price = product.discount_price if product.discount_price and product.discount_price > 0 else product.price
            sub_total = price * quantity
            total_quantity += quantity
            gross_total+=sub_total
                
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    store_id = settings.STORE_ID
    store_pass = settings.STORE_PASS
    mypayment = SSLCSession(sslc_is_sandbox=True, sslc_store_id=store_id, sslc_store_pass=store_pass)
    
    status_url = request.build_absolute_uri(reverse('status'))
    
    mypayment.set_urls(success_url=status_url, fail_url=status_url, cancel_url=status_url, ipn_url=status_url)
    
    mypayment.set_product_integration(total_amount=Decimal(gross_total), currency='BDT',
                                          product_category='User Product', product_name='None',
                                          num_of_item=total_quantity, shipping_method='online', product_profile='None')
    
    mypayment.set_customer_info(name=f"{userInfo.first_name} {userInfo.last_name}", email=userInfo.email, address1=userInfo.address, address2='',
                                    city='', postcode='none', country='Bangladesh', phone=userInfo.phone_number)
    
    mypayment.set_shipping_info(shipping_to=userInfo.email, address=userInfo.address, city='None',
                                    postcode='none', country='Bangladesh')
    
    mypayment.set_additional_values(value_a=orderId, value_b='', value_c='', value_d='')
    
    response_data = mypayment.init_payment()
    
    return response_data



@csrf_exempt
@api_view(['POST'])
def sslc_status(request):
    if request.method == 'post' or request.method == 'POST':
        payment_data = request.POST
        request_status = payment_data['status']
        
        if request_status == "VALID":
            redis_key = payment_data['value_a']
            cached_data = cache.get(redis_key)
            all_data = json.loads(cached_data)
            
            
            context_data = {
                "user_data": all_data['user'],
                "payment_data": payment_data
            }
            
            serializer = CreateOrderSerializer(data=all_data['request_data'], context={'request': context_data})
            
            if serializer.is_valid():
                serializer.save()
                return HttpResponseRedirect(f"{settings.FRONTEND_URL}/user_profile/my_orders", status=status.HTTP_303_SEE_OTHER)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif request_status == "FAILED":
            return HttpResponseRedirect(f"{settings.FRONTEND_URL}", status=status.HTTP_303_SEE_OTHER)
    
    
    

class OrderViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        try:
            order_method = request.data.get('payment_type', None) 
            
            serializer = CreateOrderSerializer(data=request.data, context={'request': request})
            
            if serializer.is_valid():
                
                if order_method == "online":
                    
                    redis_key = f"order_data:{uuid.uuid4().hex}"
                    
                    data_to_cache = {
                        "user": request.user.id,
                        "request_data": request.data
                    }
                    
                    cache.set(redis_key, json.dumps(data_to_cache), timeout=30 * 60)
                    
                    received_response = handleOnlineOrder(request, request.data, request.user, redis_key)
                    
                    return Response({
                        'payment_type': "online",
                        'response_data': received_response
                    }, status=status.HTTP_201_CREATED)
                
                
                elif order_method == "cash":
                    
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
        
