from .models import Post, Comment
from core.models import AppUser
from rest_framework import serializers
from django.db import transaction


class CreatePostSerializer(serializers.ModelSerializer):

    class Meta:
        model = Post
        fields = ['id', 'title', 'image', 'views', 'content_text', 'created_at']
        read_only_fields = ['id', 'views', 'created_at']

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        app_user = AppUser.objects.filter(user=user).first()
        if not app_user:
            raise serializers.ValidationError('User not found')
        post = Post.objects.create(post_by=app_user, views=0, **validated_data)
        return post


class UpdatePostSerializer(serializers.ModelSerializer):

    class Meta:
        model = Post
        fields = ['id', 'title', 'image', 'views', 'content_text', 'created_at', 'updated_at']
        read_only_fields = ['id', 'views', 'created_at', 'updated_at']


class PostListSerializer(serializers.ModelSerializer):
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    post_by = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id',
            'post_by',
            'title',
            'image',
            'views',
            'content_text',
            'likes_count',
            'comments_count',
            'created_at',
            'updated_at',
        ]

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_post_by(self, obj):
        return obj.post_by_id


class CreateCommentSerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Comment
        fields = ['id', 'comment_text', 'parent', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_parent(self, parent):
        if parent is None:
            return parent
        post = self.context.get('post')
        if parent.post_id != post.id:
            raise serializers.ValidationError('Parent comment must belong to the same post')
        return parent

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        post = self.context.get('post')
        app_user = AppUser.objects.filter(user=request.user).first()
        if not app_user:
            raise serializers.ValidationError('User not found')
        return Comment.objects.create(
            post=post,
            comment_by=app_user,
            **validated_data,
        )
