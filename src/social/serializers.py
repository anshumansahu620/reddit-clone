from .models import Post,Comment
from core.models import AppUser
from rest_framework import serializers
from django.db import transaction



class CreatePostSerializer(serializers.ModelSerializer):
    

    class Meta:
        model=Post
        fields = ['id', 'title', 'image', 'views', 'content_text', 'created_at']
        read_only_fields = ['id', 'views', 'created_at']

    @transaction.atomic
    def create(self,validated_data):
        reqeust=self.context.get('request')
        user=reqeust.user
        app_user=AppUser.objects.filter(user=user).first()
        if not app_user:
            return serializers.ValidationError('User not found')
        post=Post.objects.create(post_by=app_user,views=0,**validated_data)
        
        return post





