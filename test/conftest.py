import pytest
from faker import Faker
from core.models import User, Post
from services.utility import generate_uuid

fake = Faker()


@pytest.mark.django_db
@pytest.fixture
def setup_user_data():
    data = {
        'first_name': fake.first_name(),
        'last_name': fake.last_name(),
        'email': fake.email(),
        'address': fake.address(),
        'username': generate_uuid(User, 'username')
    }
    instance = User.objects.create(**data)
    assert list(data.values()) == [instance.first_name, instance.last_name, instance.email, instance.address,
                                   instance.username]
    return instance


@pytest.mark.django_db
@pytest.fixture
def setup_post_data(setup_user_data):
    data = {
        'user': setup_user_data,
        'title': fake.name(),
        'publish': True,
        'description': ' '.join(fake.sentences())
    }
    post = Post.objects.create(**data)
    return post
