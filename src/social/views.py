from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from .models import Post
from .serializers import CreatePostSerializer

class CreatePostView(CreateAPIView):
    queryset = Post.objects.all()
    serializer_class = CreatePostSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        return {'request': self.request}