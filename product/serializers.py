from rest_framework import serializers
from product.models import Category, KeyFeature, Product, Specification



class KeyFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = KeyFeature
        fields = ['name', 'value']


class SpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specification
        fields = ['category', 'name', 'value']

class ProductSerializer(serializers.ModelSerializer):
    key_features = KeyFeatureSerializer(many=True, required=False)
    specifications = SpecificationSerializer(many=True, required=False)
    category = serializers.CharField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'discount_price', 'product_code', 
                  'brand', 'category', 'image_urls', 'description', 
                  'key_features', 'specifications']

    def create(self, validated_data):
        key_features_data = validated_data.pop('key_features', [])
        specifications_data = validated_data.pop('specifications', [])
        
        category_name = validated_data.pop('category')
        
        category, _ = Category.objects.get_or_create(name=category_name)
        product = Product.objects.create(category=category, **validated_data)

        for feature_data in key_features_data:
            KeyFeature.objects.create(product=product, **feature_data)


        for specification_data in specifications_data:
            Specification.objects.create(product=product, **specification_data)

        return product

    # def update(self, instance, validated_data):
    #     key_features_data = validated_data.pop('key_features', None)
    #     specifications_data = validated_data.pop('specifications', None)

    #     # Update Product instance
    #     for attr, value in validated_data.items():
    #         setattr(instance, attr, value)
    #     instance.save()

    #     # Update related KeyFeature instances
    #     if key_features_data is not None:
    #         instance.key_features.all().delete()  # Clear existing features if you want
    #         for feature_data in key_features_data:
    #             KeyFeature.objects.create(product=instance, **feature_data)

    #     # Update related Specification instances
    #     if specifications_data is not None:
    #         instance.specifications.all().delete()  # Clear existing specifications if you want
    #         for specification_data in specifications_data:
    #             Specification.objects.create(product=instance, **specification_data)

    #     return instance
