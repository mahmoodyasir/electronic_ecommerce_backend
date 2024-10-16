from django.urls import path
from .views import ProductCreateView


urlpatterns = [
  path('create_product', ProductCreateView.as_view(), name='create_product'),
]