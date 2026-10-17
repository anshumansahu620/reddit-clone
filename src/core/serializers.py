from rest_framework import serializers
from .models import AppUser, Otp
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import transaction
from django.db.transaction import on_commit


User = get_user_model()


class AppUserRegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = AppUser
        fields = ['username', 'password', 'email', 'avatar']

    def validate(self, data):
        email = data.get('email')
        username = data.get('username')

        errors = {}

        if User.objects.filter(email=email).exists():
            errors['email'] = "Email already exists"

        if User.objects.filter(username=username).exists():
            errors['username'] = "Username already exists"

        if errors:
            raise serializers.ValidationError(errors)

        return data

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop('password')
        email = validated_data.pop('email')
        username = validated_data.pop('username')

        # Create auth user
        user = User.objects.create_user(
            email=email,
            username=username,
            password=password
        )
        user.is_active = False
        user.save()

        
        app_user = AppUser.objects.create(user=user, **validated_data)

        
        otp_code = Otp.generate_otp()
        Otp.objects.create(user=app_user, otp=otp_code)

        
        on_commit(lambda: send_mail(
            "Verify Your Account",
            f"Your OTP is {otp_code}",
            None,
            [email],
            fail_silently=False
        ))

        return app_user


class VerifyOTPSerializer(serializers.Serializer):


    email = serializers.EmailField()
    otp = serializers.IntegerField()


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField()
    new_password = serializers.CharField()


class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField()
