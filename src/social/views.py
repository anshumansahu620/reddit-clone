from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from rest_framework.generics import CreateAPIView, ListAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from core.models import AppUser
from .models import Post, Comment
from .serializers import (
    CreatePostSerializer,
    UpdatePostSerializer,
    CreateCommentSerializer,
    PostListSerializer,
)


def invalidate_recent_posts_cache():
    cache.delete(settings.RECENT_POSTS_CACHE_KEY)


class CreatePostView(CreateAPIView):
    queryset = Post.objects.all()
    serializer_class = CreatePostSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        return {'request': self.request}

    def perform_create(self, serializer):
        serializer.save()
        invalidate_recent_posts_cache()


class RecentPostsView(ListAPIView):
    """Fetch all posts created in the last hour (Redis-cached)."""

    serializer_class = PostListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        one_hour_ago = timezone.now() - timedelta(hours=1)
        return (
            Post.objects.filter(created_at__gte=one_hour_ago)
            .select_related('post_by')
            .prefetch_related('likes', 'comments')
            .order_by('-created_at')
        )

    def list(self, request, *args, **kwargs):
        cache_key = settings.RECENT_POSTS_CACHE_KEY
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        cache.set(cache_key, data, settings.RECENT_POSTS_CACHE_TTL)
        return Response(data)


class LatestPostsView(ListAPIView):
    """Fetch the latest posts (newest first). Optional ?limit=20."""

    serializer_class = PostListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            limit = int(self.request.query_params.get('limit', 20))
        except (TypeError, ValueError):
            limit = 20
        limit = max(1, min(limit, 100))
        return (
            Post.objects.all()
            .select_related('post_by')
            .prefetch_related('likes', 'comments')
            .order_by('-created_at')[:limit]
        )


class UserPostsView(ListAPIView):
    """Fetch posts by a specific AppUser id. Optional ?limit=20."""

    serializer_class = PostListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Post.objects.none()
        try:
            limit = int(self.request.query_params.get('limit', 20))
        except (TypeError, ValueError):
            limit = 20
        limit = max(1, min(limit, 100))
        user_id = self.kwargs['user_id']
        return (
            Post.objects.filter(post_by_id=user_id)
            .select_related('post_by')
            .prefetch_related('likes', 'comments')
            .order_by('-created_at')[:limit]
        )


class CreateCommentView(CreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CreateCommentSerializer
    permission_classes = [IsAuthenticated]

    def get_post(self):
        if getattr(self, 'swagger_fake_view', False):
            return None
        return Post.objects.filter(pk=self.kwargs['pk']).first()

    def get_serializer_context(self):
        return {'request': self.request, 'post': self.get_post()}

    def create(self, request, *args, **kwargs):
        post = self.get_post()
        if not post:
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)
        response = super().create(request, *args, **kwargs)
        invalidate_recent_posts_cache()
        return response


class DeleteCommentView(DestroyAPIView):
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Comment.objects.none()
        app_user = AppUser.objects.filter(user=self.request.user).first()
        if not app_user:
            return Comment.objects.none()
        return Comment.objects.filter(comment_by=app_user)

    def perform_destroy(self, instance):
        instance.delete()
        invalidate_recent_posts_cache()


class OwnerPostMixin:
    """Restrict queryset to posts owned by the authenticated AppUser."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Post.objects.none()
        app_user = AppUser.objects.filter(user=self.request.user).first()
        if not app_user:
            return Post.objects.none()
        return Post.objects.filter(post_by=app_user)


class UpdatePostView(OwnerPostMixin, UpdateAPIView):
    serializer_class = UpdatePostSerializer
    lookup_field = 'pk'

    def get_serializer_context(self):
        return {'request': self.request}

    def perform_update(self, serializer):
        serializer.save()
        invalidate_recent_posts_cache()


class DeletePostView(OwnerPostMixin, DestroyAPIView):
    lookup_field = 'pk'

    def perform_destroy(self, instance):
        instance.delete()
        invalidate_recent_posts_cache()


class LikePostView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        app_user = AppUser.objects.filter(user=request.user).first()
        if not app_user:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        post = Post.objects.filter(pk=pk).first()
        if not post:
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

        if post.likes.filter(pk=app_user.pk).exists():
            return Response({'message': 'Post already liked'}, status=status.HTTP_200_OK)

        post.likes.add(app_user)
        invalidate_recent_posts_cache()
        return Response(
            {'message': 'Post liked', 'likes_count': post.likes.count()},
            status=status.HTTP_200_OK,
        )


class UnlikePostView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        app_user = AppUser.objects.filter(user=request.user).first()
        if not app_user:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        post = Post.objects.filter(pk=pk).first()
        if not post:
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

        if not post.likes.filter(pk=app_user.pk).exists():
            return Response({'message': 'Post was not liked'}, status=status.HTTP_200_OK)

        post.likes.remove(app_user)
        invalidate_recent_posts_cache()
        return Response(
            {'message': 'Like removed', 'likes_count': post.likes.count()},
            status=status.HTTP_200_OK,
        )
