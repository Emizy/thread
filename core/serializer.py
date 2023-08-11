from django.conf import settings
from rest_framework import serializers

from core.models import User, Post, Comment


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'address']


class PostSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    image = serializers.SerializerMethodField('get_image')
    total_comments = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'user', 'title', 'slug', 'description', 'image', 'total_comments']

    @staticmethod
    def get_image(obj):
        if obj.image:
            return f'{settings.BASE_URL}{obj.image.url}'
        return ''


class CommentSerializer(serializers.ModelSerializer):
    total_replies = serializers.IntegerField(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'parent', 'post', 'body', 'timestamp', 'total_replies']
