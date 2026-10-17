from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import (
    AppUserRegisterSerializer,
    VerifyOTPSerializer,
    ResendOTPSerializer,
    ResetPasswordSerializer,
    DeleteAccountSerializer,
)
from .models import Otp, AppUser
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()

REGISTER_BODY = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['username', 'email', 'password'],
    properties={
        'username': openapi.Schema(type=openapi.TYPE_STRING, example='john_doe'),
        'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', example='john@example.com'),
        'password': openapi.Schema(type=openapi.TYPE_STRING, example='StrongPass123!'),
        'avatar': openapi.Schema(type=openapi.TYPE_STRING, format='uri', example='https://example.com/a.png'),
    },
)

VERIFY_OTP_BODY = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['email', 'otp'],
    properties={
        'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', example='john@example.com'),
        'otp': openapi.Schema(type=openapi.TYPE_INTEGER, example=123456),
    },
)

RESEND_OTP_BODY = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['email'],
    properties={
        'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', example='john@example.com'),
    },
)

RESET_PASSWORD_BODY = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['password', 'new_password'],
    properties={
        'password': openapi.Schema(type=openapi.TYPE_STRING, example='OldPass123!'),
        'new_password': openapi.Schema(type=openapi.TYPE_STRING, example='NewPass123!'),
    },
)

DELETE_ACCOUNT_BODY = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['password'],
    properties={
        'password': openapi.Schema(
            type=openapi.TYPE_STRING,
            example='YourPassword123!',
            description='Current account password to confirm deletion',
        ),
    },
)


class RegisterView(GenericAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = AppUserRegisterSerializer
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    @swagger_auto_schema(
        request_body=REGISTER_BODY,
        consumes=['application/json'],
        produces=['application/json'],
        responses={201: openapi.Response('User created')},
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            app_user = serializer.save()
            return Response({
                "message": "User created successfully",
                "user_id": app_user.id
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTP(GenericAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = VerifyOTPSerializer
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    @swagger_auto_schema(
        request_body=VERIFY_OTP_BODY,
        consumes=['application/json'],
        produces=['application/json'],
        responses={200: openapi.Response('Account verified')},
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

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

        user.is_active = True
        user.save()

        otp_obj.verified = True
        otp_obj.save()

        return Response({"message": "Account verified"}, status=200)


class ResendOtp(GenericAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ResendOTPSerializer
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    @swagger_auto_schema(
        request_body=RESEND_OTP_BODY,
        consumes=['application/json'],
        produces=['application/json'],
        responses={200: openapi.Response('OTP sent')},
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
            app_user = AppUser.objects.get(user=user)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
        except AppUser.DoesNotExist:
            return Response({"error": "AppUser not found"}, status=404)

        Otp.objects.filter(user=app_user).delete()

        otp_code = Otp.generate_otp()
        Otp.objects.create(user=app_user, otp=otp_code)

        send_mail(
            "Verify Your Account",
            f"Your OTP is {otp_code}",
            None,
            [email],
            fail_silently=False
        )

        return Response({'message': 'OTP sent successfully'}, status=200)


class ResetPassword(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ResetPasswordSerializer
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    @swagger_auto_schema(
        request_body=RESET_PASSWORD_BODY,
        consumes=['application/json'],
        produces=['application/json'],
        responses={200: openapi.Response('Password reset')},
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        password = serializer.validated_data["password"]
        new_password = serializer.validated_data["new_password"]

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
            None,
            [user.email],
            fail_silently=False
        )

        return Response({'message': 'Password reset successful'}, status=200)


class DeleteUser(GenericAPIView):
    """
    Delete the authenticated user's account.
    Uses POST so Swagger UI can accept a JSON body (DELETE bodies are often hidden).
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    serializer_class = DeleteAccountSerializer

    @swagger_auto_schema(
        operation_description="Delete your account. Requires JWT + password confirmation JSON body.",
        request_body=DELETE_ACCOUNT_BODY,
        consumes=['application/json'],
        produces=['application/json'],
        security=[{'Bearer': []}],
        responses={
            200: openapi.Response('Account deleted'),
            400: openapi.Response('Wrong password'),
            401: openapi.Response('Unauthorized'),
        },
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if not user.check_password(serializer.validated_data['password']):
            return Response({'error': 'Wrong password'}, status=status.HTTP_400_BAD_REQUEST)

        email = user.email
        user.delete()

        send_mail(
            "Account Deleted",
            "Your account has been deleted. If this wasn't you, contact support.",
            None,
            [email],
            fail_silently=False
        )

        return Response({"message": "Successfully deleted your account"}, status=200)
