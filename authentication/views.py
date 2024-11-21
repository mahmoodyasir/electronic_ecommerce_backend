from datetime import datetime
import mimetypes
import uuid
from django.conf import settings
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from product.tasks import delete_image_from_s3_task
from utils import utils

from .tasks import upload_user_image_to_s3_task
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserTokenSerializer
from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import ValidationError
from django.core.files.storage import default_storage

User = get_user_model()

class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)  
            user = serializer.save()  

            # Create refresh and access tokens
            refresh = RefreshToken.for_user(user)

            return Response({
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone_number': user.phone_number,
                    'countryInitial': user.countryInitial,
                    'address': user.address,
                    'image_url': user.image_url,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                },
                'tokens': {
                    'access': str(refresh.access_token), 
                    'refresh': str(refresh),               
                },
                'message': 'User registered successfully.',
            }, status=status.HTTP_201_CREATED)
        except ValidationError as ve:
            # Extracting error message(s) from ValidationError
            error_details = ve.detail
            error_messages = []
            for field, errors in error_details.items():
                error_messages.extend(errors)
            
            return Response({'error': error_messages[0]}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    

class UserLoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
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
        except Exception as e:
            return Response({'error': "Invalid Credentials"}, status=status.HTTP_400_BAD_REQUEST)
        
        
class AdminLoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            user = authenticate(
                request, 
                email=serializer.validated_data['email'], 
                password=serializer.validated_data['password']
            )

            if user is not None:
                if user.is_staff == True:
                    refresh = RefreshToken.for_user(user)
                    token_data = {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                else:
                    return Response({"detail": "You are not Authorized !"}, status=500)

                return Response({
                    'tokens': token_data,       
                    'user': UserTokenSerializer(user).data 
                }, status=200)
        except Exception as e:
            return Response({'error': "Invalid Credentials"}, status=status.HTTP_400_BAD_REQUEST)


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
            'user': UserTokenSerializer(user).data
        }

        return Response(token_data, status=200)
    
class UpdateUserDetails(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def put(self, request):
        user = request.user
        data = request.data
        
        if 'image' in request.FILES:
            image = request.FILES['image']
            file_type = mimetypes.guess_type(image.name)[0].split('/')[-1]
            unique_filename = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_type}"
            temp_file_path = default_storage.save(f'static/{unique_filename}', image)
            delete_image_from_s3_task.delay(user.image_url)
            upload_user_image_to_s3_task.delay(temp_file_path, unique_filename)
            image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/users/{unique_filename}"
            user.image_url = image_url
        
        
        for attr, value in data.items():
            if attr != 'image_url':
                setattr(user, attr, value)
        
        user.save()
        
        return utils.create_response(
                success=True,
                message="User Updated Successfully",
                status_code=status.HTTP_200_OK,
                data=UserTokenSerializer(user).data
            )
        
        