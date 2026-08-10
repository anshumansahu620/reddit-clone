from django.urls import path
from .views import (
    CreatePostView,
    UpdatePostView,
    DeletePostView,
    LikePostView,
    UnlikePostView,
    CreateCommentView,
    DeleteCommentView,
    RecentPostsView,
    LatestPostsView,
    UserPostsView,
)

urlpatterns = [
    path('api/create-post/', CreatePostView.as_view(), name='create-post'),
    path('api/edit-post/<uuid:pk>/', UpdatePostView.as_view(), name='edit-post'),
    path('api/delete-post/<uuid:pk>/', DeletePostView.as_view(), name='delete-post'),
    path('api/like-post/<uuid:pk>/', LikePostView.as_view(), name='like-post'),
    path('api/unlike-post/<uuid:pk>/', UnlikePostView.as_view(), name='unlike-post'),
    path('api/add-comment/<uuid:pk>/', CreateCommentView.as_view(), name='add-comment'),
    path('api/delete-comment/<uuid:pk>/', DeleteCommentView.as_view(), name='delete-comment'),
    path('api/recent-posts/', RecentPostsView.as_view(), name='recent-posts'),
    path('api/latest-posts/', LatestPostsView.as_view(), name='latest-posts'),
    path('api/user-posts/<int:user_id>/', UserPostsView.as_view(), name='user-posts'),
]
