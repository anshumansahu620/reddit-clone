from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .views import RegisterView,VerifyOTP,ResendOtp,DeleteUser
from rest_framework.throttling import ScopedRateThrottle
from django.urls import path 

class MyTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'
    serializer_class = TokenObtainPairSerializer

urlpatterns = [
    path('api/register/',RegisterView.as_view(),name='register'),
    path('api/verify-otp/',VerifyOTP.as_view(),name='verify-otp'),
    path('api/resend-otp/',ResendOtp.as_view(),name='resend-otp'),
    path('api/delete-acc/',DeleteUser.as_view(),name='delete-user'),
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
]

