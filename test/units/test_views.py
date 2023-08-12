import os

import pytest
from django.conf import settings
from faker import Faker
from core.models import Post
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
    def test_list_comment(self, client):
        pass

    def test_list_comment_without_post_id_query(self, client):
        pass

    def test_list_comment_replies(self, client):
        pass

    def test_create_comment_reply(self, auth_client):
        pass
