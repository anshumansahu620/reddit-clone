from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny,IsAuthenticated
from .serializers import AppUserRegisterSerializer
from .models import User,Otp
from django.core.mail import send_mail
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class RegisterView(APIView):
    def post(self, request):
        serializer = AppUserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "User created successfully",
                "user_id": user.id
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    



class VerifyOTP(APIView):

    permission_classes=[AllowAny]

    def post(self,request):

        email=request.data.get("email")
        otp=request.data.get("otp")

        user=User.objects.filter(email=email).first()

        if not user:
            return Response({"error":"User not found"},status=404)
      
        otp_obj=Otp.objects.filter(user=user,otp=otp).last()

        if not otp_obj:
            return Response({"error":"Invalid OTP"},status=400)

        if otp_obj.is_expired():
            return Response({"error":"OTP expired"},status=400)

        user.is_active=True
        user.save()

        otp_obj.is_verified=True
        otp_obj.save()

        return Response({"message":"Account verified"})    
    

class ResendOtp(APIView):
    permission_classes=[AllowAny]
    def post(self,request):
        email=request.data.get('email')
        if not email:
            return Response({'email not provieded '},status=400)

        try:
            user=User.objects.get(email=email)
        except User.DoesNotExist:     
            return Response({"error":"User not found"},status=404)
        Otp.objects.filter(user=user).delete()
        otp_code=Otp.generate_otp()
        Otp.objects.create(user=user,otp=otp_code)
        send_mail(
            
            "Verify Your Account",
            f"Your OTP is {otp_code}",
            "noreply@attendance.com",
            [email],
            fail_silently=False
        )

        return Response({'message':'otp sent to email sucessfully'},status=200)

class ResetPassword(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        password = request.data.get('password')
        new_password = request.data.get('new_password')

        # Validate input
        if not password or not new_password:
            return Response({'error': 'Both passwords are required'}, status=400)

        # Check current password
        if not user.check_password(password):
            return Response({'error': 'Wrong password'}, status=400)

        # Validate new password strength
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response({'error': e.messages}, status=400)

        # Set new password
        user.set_password(new_password)
        user.save()

        # Send notification email
        send_mail(
            "Password Changed Successfully",
            "Your password has been changed. If this wasn't you, please contact support immediately.",
            "noreply@attendance.com",
            [user.email],
            fail_silently=False
        )

        return Response({'message': 'Password reset successful'}, status=200)

        