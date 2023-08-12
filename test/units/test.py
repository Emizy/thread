import pytest
from django.utils.text import slugify
from faker import Faker
from core.models import Post, Comment
from core.serializer import UserSerializer, PostSerializer, CommentSerializer

fake = Faker()


@pytest.mark.django_db
def test_user_model_with_serializer(setup_user_data):
    instance, _ = setup_user_data
    serializer = UserSerializer(instance).data
    assert [instance.id, instance.first_name, instance.last_name] == [serializer.get('id'),
                                                                      serializer.get('first_name'),
                                                                      serializer.get('last_name')]


class TestPostComment:
    @pytest.mark.django_db
    def test_post_model(self, setup_user_data):
        user, _ = setup_user_data
        data = {
            'user': user,
            'title': fake.name(),
            'publish': True,
            'description': ' '.join(fake.sentences())
        }
        post = Post.objects.create(**data)
        slug = slugify(data.get('title'))
        assert slug == post.slug

    @pytest.mark.django_db
    def test_post_serializer(self, setup_user_data):
        user, _ = setup_user_data
        data = {
            'user': user,
            'title': fake.name(),
            'publish': True,
            'description': ' '.join(fake.sentences())
        }
        post = Post.objects.create(**data)
        serializer = PostSerializer(post).data
        assert serializer.get('title') == post.title

    @pytest.mark.django_db
    def test_post_comment_comment(self, setup_post_data, setup_user_data):
        post, _ = setup_post_data
        user, _ = setup_user_data
        for _ in range(5):
            comment = {
                'post': post,
                'user': user,
                'body': ' '.join(fake.sentences())
            }
            _ = Comment.objects.create(**comment)
        post.refresh_from_db()
        assert post.total_comments == 5

    @pytest.mark.django_db
    def test_post_comment_serializer(self, setup_post_data, setup_user_data):
        post, _ = setup_post_data
        user, _ = setup_user_data
        for _ in range(5):
            comment = {
                'post': post,
                'user': user,
                'body': ' '.join(fake.sentences())
            }
            _ = Comment.objects.create(**comment)
        comments = Comment.objects.filter(post=post)
        _ = CommentSerializer(comments, many=True).data
        assert comments.count() == 5
