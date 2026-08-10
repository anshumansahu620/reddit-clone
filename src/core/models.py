from django.db import models
from django.utils import timezone
from datetime import datetime, time, timedelta
from django.contrib.auth import get_user_model
import random

User = get_user_model()


class AppUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.user.username


class Otp(models.Model):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)  # ✅ FIXED
    otp = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)

    def is_expired(self):
        created = self.created_at
        # Legacy DB column was TIME; coerce so expiry math works
        if isinstance(created, time):
            created = timezone.make_aware(datetime.combine(timezone.localdate(), created))
        elif timezone.is_naive(created):
            created = timezone.make_aware(created)
        return timezone.now() > created + timedelta(minutes=60)

    @staticmethod
    def generate_otp():
        return random.randint(100000, 999999)



class FollowingTable(models.Model):
    app_user = models.OneToOneField(
        AppUser,
        on_delete=models.CASCADE,
        related_name='following_table',
    )
    followers = models.ManyToManyField(
        AppUser,
        related_name='follower_of',
        blank=True,
    )
    following = models.ManyToManyField(
        AppUser,
        related_name='followed_by',
        blank=True,
    )

