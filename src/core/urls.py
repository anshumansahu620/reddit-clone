from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import RegisterView,VerifyOTP,ResendOtp

from django.urls import path 

urlpatterns = [
    path('api/register/',RegisterView.as_view(),name='register'),
    path('api/verify-otp/',VerifyOTP.as_view(),name='verify-otp'),
    path('api/resend-otp/',ResendOtp.as_view(),name='resend-otp'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
]

