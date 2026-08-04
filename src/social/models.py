from django.db import models
from core.models import AppUser
import uuid





class Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    post_by = models.ForeignKey(
        AppUser, 
        on_delete=models.CASCADE, 
        related_name='posts'
    )

    title = models.CharField(max_length=200)
    
    likes = models.ManyToManyField(
        AppUser, 
        related_name='liked_posts', 
        blank=True
    )

    image = models.ImageField(
        upload_to='images/', 
        blank=True, 
        null=True
    )

    views=models.PositiveIntegerField()

    content_text = models.TextField(max_length=5000)

    created_at = models.DateTimeField(auto_now_add=True)  # useful
    updated_at = models.DateTimeField(auto_now=True)      # useful

    def __str__(self):
        return self.title









class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    comment_by = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    comment_text = models.TextField(max_length=500)

    likes = models.ManyToManyField(
        AppUser,
        related_name='liked_comments',
        blank=True
    )

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.comment_by} - {self.comment_text[:20]}"


class Report(models.Model):
    reported_by= models.ForeignKey(AppUser, on_delete=models.CASCADE)
    post=models.ForeignKey(Post,null=True, on_delete=models.CASCADE)
    comment=models.ForeignKey(Comment,null=True, on_delete=models.CASCADE)

    created_at=models.DateTimeField(auto_now_add=True)


