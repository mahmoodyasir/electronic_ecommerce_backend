from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')

urlpatterns = [
    path("", include(router.urls)),
  # path('create_product', ProductCreateView.as_view(), name='create_product'),
  # path('get_product', ProductListView.as_view(), name='get_product'),
  # path('get_single_product/<int:id>', ProductDetailView.as_view(), name='get_single_product'),
]