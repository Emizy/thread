from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    address = models.TextField(default="", null=True, blank=True)
    avatar = models.ImageField(upload_to="profile", null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.get_full_name()} - {self.email}'


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="%(class)s")
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    image = models.ImageField(upload_to='blog')
    description = models.TextField(default='')
    publish = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id} {self.title}"

    class Meta:
        verbose_name_plural = 'Posts'

    @property
    def total_comments(self):
        return self.comments.all().count()


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments", null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="%(class)s", null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name="%(class)s", null=True, blank=True)
    body = models.TextField(default='')
    timestamp = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        parent_id = self.parent.id if self.parent is not None else ''
        name = self.post.title if self.post is not None else f'<Comment Reply> #{parent_id}'
        return f"{name}"

    class Meta:
        verbose_name_plural = 'Comments'

    @property
    def total_replies(self):
        return Comment.objects.filter(parent=self).count()
