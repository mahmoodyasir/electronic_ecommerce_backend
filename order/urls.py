from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from .views import sslc_status

router = DefaultRouter()
router.register('orders', OrderViewSet, basename='orders')

urlpatterns = [
    path("", include(router.urls)),
    path('sslc/status/', sslc_status, name='status'),
]