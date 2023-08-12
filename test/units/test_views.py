import os
import random
import pytest
from django.conf import settings
from faker import Faker
from core.models import Post, Comment, User
from test.endpoints import EndPoint

fake = Faker()
file = os.path.join(settings.BASE_DIR, r'test/dummy/blank.jpg')


@pytest.mark.django_db
class TestAuthentication:

    def test_user_create_account_success(self, client, dummy_user_data):
        payload = dummy_user_data
        response = client.post(f'{EndPoint.REGISTER}', payload, format='json')
        assert response.status_code == 201 and response.data['message'] == 'Account created successfully'

    def test_user_create_account_fail(self, client):
        """
        This test case handle testing if serializer validation for each field is working
        """
        payload = {
            "first_name": fake.first_name(),
            "last_name": "",
            "email": "",
            "password": fake.password(10)
        }
        response = client.post(f'{EndPoint.REGISTER}', payload, format='json')
        assert response.status_code == 400

    def test_user_create_account_email_already_exist(self, client, dummy_user_data):
        """
        This test case handle testing the uniqueness of email
        """
        payload = dummy_user_data
        _ = client.post(f'{EndPoint.REGISTER}', payload, format='json')
        _response = client.post(f'{EndPoint.REGISTER}', payload, format='json')
        data = _response.data
        assert 'Email already exist' in str(data)


@pytest.mark.django_db
class TestPost:
    def test_list_post(self, client, dummy_posts):
        _ = dummy_posts
        response = client.get(f'{EndPoint.POST}/', format='json')
        data = response.data['data']['results']
        assert len(data) == 3

    def test_list_post_with_filter_by_user_id(self, client, dummy_posts):
        user, _ = dummy_posts
        response = client.get(f'{EndPoint.POST}/?user__id={user.id}', format='json')
        data = response.data['data']['results']
        assert len(data) >= 3

    def test_list_post_with_filter_by_invalid_user_id(self, client, dummy_posts):
        user, _ = dummy_posts
        response = client.get(f'{EndPoint.POST}/?user__id=6', format='json')
        data = response.data['data']['results']
        assert len(data) == 0

    def test_list_post_with_filter_by_publish_status(self, client, dummy_posts):
        user, _ = dummy_posts
        response = client.get(f'{EndPoint.POST}/?publish=0', format='json')
        data = response.data['data']['results']
        assert len(data) == 0

    def test_post_create(self, auth_client):
        with open(file, 'rb') as image:
            payload = {
                'title': fake.name(),
                'image': image,
                'publish': True,
                'description': ' '.join(fake.sentences())
            }
            response = auth_client.post(f'{EndPoint.POST}/', data=payload, format='multipart')
            assert response.status_code == 201

    def test_post_create_with_non_authenticated_request(self, client):
        with open(file, 'rb') as image:
            payload = {
                'title': fake.name(),
                'image': image,
                'publish': True,
                'description': ' '.join(fake.sentences())
            }
            response = client.post(f'{EndPoint.POST}/', data=payload, format='multipart')
            print(response.data)
            assert response.status_code == 401

    def test_post_update(self, auth_client):
        with open(file, 'rb') as image:
            payload = {
                'title': fake.name(),
                'image': image,
                'publish': True,
                'description': ' '.join(fake.sentences())
            }
            _ = auth_client.post(f'{EndPoint.POST}/', data=payload, format='multipart')
        post = Post.objects.all().first()
        payload = {
            'title': fake.name(),
            'description': ' '.join(fake.sentences())
        }
        response = auth_client.put(f'{EndPoint.POST}/{post.id}/', data=payload, format='json')
        data = response.data['data']
        assert list(payload.values()) == [data.get('title'), data.get('description')]

    def test_post_delete(self, auth_client):
        payload = {
            'title': fake.name(),
            'publish': True,
            'description': ' '.join(fake.sentences())
        }
        _ = auth_client.post(f'{EndPoint.POST}/', data=payload, format='multipart')
        post = Post.objects.all().first()
        response = auth_client.delete(f'{EndPoint.POST}/{post.id}/', format='json')
        assert response.status_code == 204


@pytest.mark.django_db
class TestPostComment:
    @staticmethod
    def prepare_dummy_comment_data(no_of_data: int, user, post):
        for i in range(no_of_data):
            comment = {
                'post': post,
                'user': user,
                'body': ' '.join(fake.sentences())
            }
            _ = Comment.objects.create(**comment)

    def test_list_comment(self, client, setup_post_data):
        # prepare
        post, user_info = setup_post_data
        user = User.objects.get(email=user_info.get('email'))
        self.prepare_dummy_comment_data(no_of_data=10, user=user, post=post)
        # act
        response = client.get(f'{EndPoint.COMMENT}/?post__id={post.id}&limit=10', format='json')
        results = response.data['data']['results']
        # assert
        assert response.status_code == 200
        assert len(results) == 10

    def test_list_comment_without_post_id_query(self, client, setup_post_data):
        post, user_info = setup_post_data
        user = User.objects.get(email=user_info.get('email'))
        self.prepare_dummy_comment_data(no_of_data=10, user=user, post=post)
        response = client.get(f'{EndPoint.COMMENT}/?limit=10', format='json')
        results = response.data['data']['results']
        assert len(results) == 0

    def test_list_comment_replies(self, client, setup_post_data, setup_user_data):
        post, user_info = setup_post_data
        user_instance, _ = setup_user_data
        user = User.objects.get(email=user_info.get('email'))
        self.prepare_dummy_comment_data(no_of_data=1, user=user, post=post)
        comment = Comment.objects.all().first()
        users = [user, user_instance]
        for _ in range(10):
            random.shuffle(users)
            data = {
                'parent_comment_id': comment.id,
                'body': fake.sentence(),
                'user': users[0]
            }
            _ = Comment.objects.create(**data)
        response = client.get(f'{EndPoint.COMMENT}/{comment.id}/replies/')
        data = response.data['data']
        assert len(data) == 10

    def test_create_comment_reply(self, auth_client, setup_post_data):
        post, user_info = setup_post_data
        user = User.objects.get(email=user_info.get('email'))
        self.prepare_dummy_comment_data(no_of_data=1, user=user, post=post)
        comment = Comment.objects.all().first()
        data = {
            'parent_comment_id': comment.id,
            'body': fake.sentence(),
        }
        response = auth_client.post(f'{EndPoint.COMMENT}/', data, 'json')
        assert response.status_code == 201

    def test_create_comment_without_post_id(self, auth_client):
        data = {
            'body': fake.sentence(),
        }
        response = auth_client.post(f'{EndPoint.COMMENT}/', data, 'json')
        assert response.status_code == 400
