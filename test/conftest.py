import pytest
from rest_framework.test import APIClient
from faker import Faker
from core.models import User, Post
from services.utility import generate_uuid
from test.endpoints import EndPoint

fake = Faker()


@pytest.fixture
def client():
    """
    api client to be used as a fixture in making request to the endpoints
    """
    return APIClient()


@pytest.fixture
def auth_client(client, setup_user_data):
    user, user_info = setup_user_data
    payload = {
        'username': user_info.get('email'),
        'password': user_info.get('password')
    }
    response = client.post(EndPoint.LOGIN, payload, 'json')
    data = response.data
    assert 'token' in data
    client.credentials(HTTP_AUTHORIZATION='Bearer ' + data['token']['access'])
    return client


@pytest.mark.django_db
@pytest.fixture
def setup_user_data():
    data = {
        'first_name': fake.first_name(),
        'last_name': fake.last_name(),
        'email': fake.email(),
        'address': fake.address(),
        'username': generate_uuid(User, 'username'),
        'password': '123456'
    }
    instance = User.objects.create_user(username=data.get('username'), email=data.get('email'),
                                        password=data.get('password'), **{
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name'),
            'address': data.get('address'),
        })
    assert [data.get('first_name'), data.get('last_name'), data.get('email'), data.get('username')] == [
        instance.first_name, instance.last_name, instance.email, instance.username]
    return instance, data


@pytest.fixture
def dummy_user_data():
    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.email(),
        "address": fake.address(),
        "password": fake.password(10)
    }


@pytest.mark.django_db
@pytest.fixture
def dummy_posts(setup_user_data):
    user, _ = setup_user_data
    for i in range(5):
        data = {
            'user': user,
            'title': fake.name(),
            'publish': True,
            'description': ' '.join(fake.sentences())
        }
        _ = Post.objects.create(**data)
    return user, Post.objects.filter(user=user)


@pytest.mark.django_db
@pytest.fixture
def setup_post_data(setup_user_data):
    user, user_info = setup_user_data
    data = {
        'user': user,
        'title': fake.name(),
        'publish': True,
        'description': ' '.join(fake.sentences())
    }
    post = Post.objects.create(**data)
    return post, user_info
