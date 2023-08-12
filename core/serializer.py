from django.conf import settings
from rest_framework import serializers

from core.models import User, Post, Comment
from services.utility import generate_uuid


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
        fields = ['id', 'user', 'title', 'slug', 'description', 'image', 'publish', 'total_comments']

    @staticmethod
    def get_image(obj):
        if obj.image:
            return f'{settings.BASE_URL}{obj.image.url}'
        return ''


class CommentSerializer(serializers.ModelSerializer):
    total_replies = serializers.IntegerField(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'parent_comment_id', 'post_id', 'body', 'timestamp', 'total_replies']


class UserRegisterFormSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(max_length=255)
    address = serializers.CharField(required=False)
    password = serializers.CharField(required=True)

    def create(self, validated_data):
        instance = User.objects.create_user(username=generate_uuid(User, 'username'),
                                            email=validated_data.get('email'),
                                            password=validated_data.get('password'),
                                            **{
                                                'first_name': validated_data.get('first_name', ''),
                                                'last_name': validated_data.get('last_name', ''),
                                                'address': validated_data.get('address', ''),
                                            })
        return instance

    def update(self, instance, validated_data):
        pass

    def validate(self, attrs):
        if User.objects.filter(email=attrs.get('email')).exists() is True:
            raise serializers.ValidationError('Email already exist')
        return attrs


class LoginFormSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, help_text='Username could be either customer email or system '
                                                              'generated username for the user')
    password = serializers.CharField(required=True)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class PostFormSerializer(serializers.Serializer):
    title = serializers.CharField(required=True)
    description = serializers.CharField(required=True)
    image = serializers.ImageField(required=False)
    publish = serializers.BooleanField(required=False)

    def create(self, validated_data):
        instance = Post.objects.create(**validated_data)
        if self.context["request"].FILES.get('image'):
            instance.image = self.context["request"].FILES['image']
            instance.save(update_fields=['image'])
        return instance

    def update(self, instance, validated_data):
        _ = Post.objects.filter(id=instance.id).update(**validated_data)
        instance.refresh_from_db()
        if self.context["request"].FILES.get('image'):
            instance.image = self.context["request"].FILES['image']
            instance.save(update_fields=['image'])
        return instance


class CommentFormSerializer(serializers.Serializer):
    post_id = serializers.CharField(required=False)
    parent_comment_id = serializers.CharField(required=False)
    body = serializers.CharField(required=True)

    def create(self, validated_data):
        instance = Comment.objects.create(**validated_data)
        return instance

    def update(self, instance, validated_data):
        pass

    def validate(self, attrs):
        if bool(attrs.get('post_id')) is False and bool(attrs.get('parent_comment_id')) is False:
            raise serializers.ValidationError(
                'post_id or parent_comment_id is required to add a comment')
        if bool(attrs.get('post_id')) is False and bool(attrs.get('parent_comment_id')) is False:
            raise serializers.ValidationError('Kindly supply either post_id or parent_comment_id to add a comment')

        if bool(attrs.get('post_id')):
            if Post.objects.filter(id=attrs.get('post_id')).exists() is False:
                raise serializers.ValidationError(f"Supply post id ({attrs.get('post_id')}) does not exist")
        if bool(attrs.get('parent_comment_id')):
            if Comment.objects.filter(id=attrs.get('parent_comment_id')).exists() is False:
                raise serializers.ValidationError(f"Supply parent comment id "
                                                  f"({attrs.get('parent_comment_id')}) does not exist")
        return attrs
