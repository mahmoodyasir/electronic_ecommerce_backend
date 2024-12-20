from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, SpecificationView, KeyFeatureView, ProductFilterView, UpdateProductImagesView, ProductCreateView

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')

urlpatterns = [
    path("", include(router.urls)),
    path('product-create', ProductCreateView.as_view(), name='product-create'),
    path('products/get_feature', KeyFeatureView.as_view(), name='get_feature'),
    path('products/get_specifications', SpecificationView.as_view(), name='get_specifications'),
    path('products/filter', ProductFilterView.as_view(), name='filter'),
    path('products/image_update/<int:pk>', UpdateProductImagesView.as_view(), name='image_update'),
  # path('get_single_product/<int:id>', ProductDetailView.as_view(), name='get_single_product'),
]