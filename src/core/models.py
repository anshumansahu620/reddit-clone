from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
import random

# Create your models here.


class AppUser(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    avatar=models.URLField(blank=True,null=True)


    def __str__(self):
        return self.user.username


class Otp(models.Model):
    user=models.ForeignKey(User,  on_delete=models.CASCADE)
    otp=models.IntegerField()
    created_at=models.DateTimeField( blank=True,auto_now_add=True)
    verified=models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now()> self.created_at+timedelta(minutes=60)
    
    @staticmethod
    def generate_otp():
        return str(random.randint(100000,999999))
    







