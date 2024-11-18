from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from authentication.views import UserDetailView, UserLoginView, UserRegistrationView, AdminLoginView, UpdateUserDetails

urlpatterns = [
    path('register', UserRegistrationView.as_view(), name='register'),
    path('login', UserLoginView.as_view(), name='login'),
    path('admin_login', AdminLoginView.as_view(), name='admin_login'),
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('get_user', UserDetailView.as_view(), name='get_user'),
    path('update_user', UpdateUserDetails.as_view(), name='update_user'),
]