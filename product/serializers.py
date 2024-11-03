from rest_framework import serializers
from inventory.models import Inventory
from product.models import Category, KeyFeature, Product, Specification



class KeyFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = KeyFeature
        fields = ['name', 'value']


class SpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specification
        fields = ['category', 'name', 'value']
        
        
class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = ['quantity', 'restock_alert', 'last_restocked'] 
        

class ProductSerializer(serializers.ModelSerializer):
    key_features = KeyFeatureSerializer(many=True, required=False)
    specifications = SpecificationSerializer(many=True, required=False)
    inventory_product = InventorySerializer(required=False)
    product_code = serializers.CharField(required=False)
    isActive = serializers.BooleanField(required=False)
    isHighlighted = serializers.BooleanField(required=False)
    category = serializers.CharField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'discount_price', 'product_code', 
                  'brand', 'category', 'image_urls', 'description', 
                  'key_features', 'specifications', 'inventory_product', 'isActive', 'isHighlighted']

    def create(self, validated_data):
        key_features_data = validated_data.pop('key_features', [])
        specifications_data = validated_data.pop('specifications', [])
        inventory_data = validated_data.pop('inventory_product', {})
        category_name = validated_data.pop('category')
        
        category, _ = Category.objects.get_or_create(name=category_name)
        product = Product.objects.create(category=category, **validated_data)

        for feature_data in key_features_data:
            KeyFeature.objects.create(product=product, **feature_data)


        for specification_data in specifications_data:
            Specification.objects.create(product=product, **specification_data)
        
        if inventory_data:
            Inventory.objects.create(product=product, **inventory_data)

        return product

    def update(self, instance, validated_data):
        key_features_data = validated_data.pop('key_features', None)
        specifications_data = validated_data.pop('specifications', None)
        inventory_data = validated_data.pop('inventory_product', {})
        category_name = validated_data.pop('category')


        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        if category_name:
            category, _ = Category.objects.get_or_create(name=category_name)
            instance.category = category

    
        if key_features_data is not None:
            instance.key_features.all().delete()  
            for feature_data in key_features_data:
                KeyFeature.objects.create(product=instance, **feature_data)


        if specifications_data is not None:
            instance.specifications.all().delete() 
            for specification_data in specifications_data:
                Specification.objects.create(product=instance, **specification_data)
                
                
        if inventory_data:
            Inventory.objects.update_or_create(product=instance, defaults=inventory_data)
                  
        instance.save()

        return instance
