from rest_framework import serializers

from authentication.serializers import UserSerializer
from product.serializers import ProductSerializer
from .models import OnlinePayment, Order, OrderItem, Product
from django.contrib.auth import get_user_model

User = get_user_model()

class CreateOrderSerializer(serializers.Serializer):
    shipping_address = serializers.CharField(required=True, max_length=255)
    payment_type = serializers.CharField(required=False, default="cash")
    products = serializers.DictField(
        child=serializers.IntegerField(min_value=1),  # Product ID (key) and Quantity (value)
        required=True
    )

    def validate_products(self, value):
        """Ensuring all product IDs exist and quantities are valid."""
        product_ids = value.keys()
        products = Product.objects.filter(id__in=product_ids, isActive=True)

        if len(products) != len(product_ids):
            raise serializers.ValidationError("Some products do not exist or are inactive.")
        return value

    def create(self, validated_data):
        payment_type = validated_data['payment_type']
        
        online_order = {}
        order = {}
        main_data = self.context['request']
        payment_data = ""
        
        if payment_type == "cash":
            user = self.context['request'].user
        elif payment_type == "online":
            user = User.objects.get(id=main_data.get('user_data', None))
            
        shipping_address = validated_data['shipping_address']
        payment_type = validated_data['payment_type']
        products_data = validated_data['products']

        # Create a new order
        if payment_type == "cash":
            order = Order.objects.create(
                user=user,
                shipping_address=shipping_address,
                payment_type=payment_type,
                total=0,
            )
        
        elif payment_type == "online":
            payment_data = main_data.get('payment_data', None)
            
            order = Order.objects.create(
                user=user,
                shipping_address=shipping_address,
                payment_type=payment_type,
                payment_complete=True,
                status="processing",
                total=0,
            )
            
            online_order = OnlinePayment.objects.create(
                order=order,
                transaction_id=payment_data['tran_id'],
                card_brand=payment_data['card_brand'],
                card_issuer=payment_data['card_issuer'],
                total_paid=payment_data['amount'],
                currency=payment_data['currency'],
            )

        gross_total = 0

        for product_id, quantity in products_data.items():
            try:
                # Ensure the product is active
                product = Product.objects.get(id=product_id, isActive=True)

                # Create the OrderItem and store it
                order_item = OrderItem(order=order, product=product, quantity=quantity)
                order_item.save()  # Save the OrderItem instance, which also updates inventory and calculates subtotal
                gross_total += order_item.sub_total  # Use the calculated sub_total from OrderItem
                
            except Product.DoesNotExist:
                raise serializers.ValidationError(f"Product with ID {product_id} does not exist.")
            except Exception as e:
                raise serializers.ValidationError(f"Error creating OrderItem: {str(e)}")

        order.total = gross_total
        order.save()
        if payment_data == "online":
            online_order.save()
            response = {
                "order_data": order,
                "online_order_data": online_order
            }
            return response
        else:
            return order

        



class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'sub_total']
        depth = 1
        
class OnlinePaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnlinePayment
        fields = "__all__"
        depth = 1
        

class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    items = OrderItemSerializer(many=True, required=False)
    online_payment = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ["user", "id", "order_ID", "shipping_address", "payment_complete", "payment_type", "total", "status", "created_at", "updated_at", "items", "online_payment"]
        depth = 1
        
    def get_online_payment(self, obj):
        online_payment = obj.online_payment.first()
        if online_payment:
            return OnlinePaymentSerializer(online_payment).data
        return None