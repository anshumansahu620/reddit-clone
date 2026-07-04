from rest_framework import serializers
from .models import AppUser,Otp
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import transaction

class AppUserRegisterSerializer(serializers.ModelSerializer):
    
    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)
    
   
    
    class Meta:
        model=AppUser
        fields=['username','password','email','avatar']

    @transaction.atomic
    def create(self,validated_data):
        password=validated_data.pop('password')
        email=validated_data.pop('email')
        username=validated_data.pop('username')
        user=User.objects.create(email=email,username=username,password=password)
        user.is_active=False
        user.save()

        app_user=AppUser.objects.create(user=user,**validated_data)

        otp_code=Otp.generate_otp()
        otp=Otp.objects.create(user=user,otp=otp_code)
        send_mail(
            
            "Verify Your Account",
            f"Your OTP is {otp_code}",
            "noreply@attendance.com",
            [email],
            fail_silently=False
        )
        

        


        
        app_user.save()
        return app_user
    

    