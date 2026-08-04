from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import AppUserRegisterSerializer
from .models import Otp, AppUser
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AppUserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            app_user = serializer.save()
            return Response({
                "message": "User created successfully",
                "user_id": app_user.id
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTP(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "User not found"}, status=404)

        app_user = AppUser.objects.filter(user=user).first()
        if not app_user:
            return Response({"error": "AppUser not found"}, status=404)

        otp_obj = Otp.objects.filter(user=app_user, otp=otp).last()

        if not otp_obj:
            return Response({"error": "Invalid OTP"}, status=400)

        if otp_obj.is_expired():
            return Response({"error": "OTP expired"}, status=400)

        # Activate user
        user.is_active = True
        user.save()

        # Mark OTP verified ✅ FIXED
        otp_obj.verified = True
        otp_obj.save()

        return Response({"message": "Account verified"}, status=200)


class ResendOtp(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response({'error': 'Email not provided'}, status=400)

        try:
            user = User.objects.get(email=email)
            app_user = AppUser.objects.get(user=user)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
        except AppUser.DoesNotExist:
            return Response({"error": "AppUser not found"}, status=404)

        # Delete old OTPs
        Otp.objects.filter(user=app_user).delete()

        # Create new OTP
        otp_code = Otp.generate_otp()
        Otp.objects.create(user=app_user, otp=otp_code)

        send_mail(
            "Verify Your Account",
            f"Your OTP is {otp_code}",
            "noreply@attendance.com",
            [email],
            fail_silently=False
        )

        return Response({'message': 'OTP sent successfully'}, status=200)


class ResetPassword(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        password = request.data.get('password')
        new_password = request.data.get('new_password')

        if not password or not new_password:
            return Response({'error': 'Both passwords are required'}, status=400)

        if not user.check_password(password):
            return Response({'error': 'Wrong password'}, status=400)

        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response({'error': e.messages}, status=400)

        user.set_password(new_password)
        user.save()

        send_mail(
            "Password Changed Successfully",
            "Your password has been changed. If this wasn't you, contact support.",
            "noreply@attendance.com",
            [user.email],
            fail_silently=False
        )

        return Response({'message': 'Password reset successful'}, status=200)


class DeleteUser(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        email = user.email

        user.delete()

        send_mail(
            "Account Deleted",
            "Your account has been deleted. If this wasn't you, contact support.",
            "noreply@attendance.com",
            [email],
            fail_silently=False
        )

        return Response({"message": "Successfully deleted your account"}, status=200)