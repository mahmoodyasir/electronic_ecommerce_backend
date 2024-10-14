from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from authentication.views import UserDetailView, UserLoginView, UserRegistrationView

urlpatterns = [
    path('register', UserRegistrationView.as_view(), name='register'),
    path('login', UserLoginView.as_view(), name='login'),
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('get_user', UserDetailView.as_view(), name='get_user'),
]