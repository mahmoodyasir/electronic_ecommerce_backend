from rest_framework import serializers

from authentication.serializers import UserSerializer
from product.serializers import ProductSerializer
from .models import Order, OrderItem, Product

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
        user = self.context['request'].user
        shipping_address = validated_data['shipping_address']
        payment_type = validated_data['payment_type']
        products_data = validated_data['products']

        # Create a new order
        order = Order.objects.create(
            user=user,
            shipping_address=shipping_address,
            payment_type=payment_type,
            total=0,
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

        return order



class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'sub_total']
        depth = 1
        

class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    items = OrderItemSerializer(many=True, required=False)
    
    class Meta:
        model = Order
        fields = ["user", "id", "order_ID", "shipping_address", "payment_complete", "payment_type", "total", "status", "created_at", "updated_at", "items"]
        depth = 1