from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserTokenSerializer
from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

User = get_user_model()

class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)  # Validate the data
            user = serializer.save()  # Create the user

            # Create refresh and access tokens
            refresh = RefreshToken.for_user(user)

            return Response({
                'user': {
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone_number': user.phone_number,
                    'address': user.address,
                    'image_url': user.image_url,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                },
                'tokens': {
                    'access': str(refresh.access_token),  # Access token
                    'refresh': str(refresh),               # Refresh token
                },
                'message': 'User registered successfully.',
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    

class UserLoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request, 
            email=serializer.validated_data['email'], 
            password=serializer.validated_data['password']
        )

        if user is not None:
            refresh = RefreshToken.for_user(user)
            token_data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }

            return Response({
                'tokens': token_data,       
                'user': UserTokenSerializer(user).data 
            }, status=200)
        else:
            return Response({"detail": "Invalid credentials"}, status=401)


class UserDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, *args, **kwargs):
        user = request.user
        
        refresh = RefreshToken.for_user(user)

        token_data = {
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            },
            'user': {
                'username': str(user.username),
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone_number': user.phone_number or '',
                'address': user.address or '',
                'image_url': user.image_url or '',
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
            }
        }

        return Response(token_data, status=200)