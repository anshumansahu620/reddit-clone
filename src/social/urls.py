from django.urls import path
from .views import CreatePostView

urlpatterns = [
    path('api/create-post/', CreatePostView.as_view(), name='create-post'),
]