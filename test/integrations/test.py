import pytest
import os
from django.conf import settings
from faker import Faker

from test.endpoints import EndPoint

file = os.path.join(settings.BASE_DIR, r'test/dummy/blank.jpg')
fake = Faker()


@pytest.mark.django_db
class TestIntegration:

    def test_authentication_integration(self, client, dummy_user_data):
        payload = dummy_user_data
        payload.update({'password': '1234567890'})
        response = client.post(f'{EndPoint.REGISTER}', payload, format='json')
        assert response.status_code == 201 and response.data['message'] == 'Account created successfully'
        login_response = client.post(f'{EndPoint.LOGIN}', {
            'username': payload.get('email'),
            'password': payload.get('password')
        }, 'json')
        data = login_response.data
        assert 'token' in data

    def test_post_integration(self, client, auth_client):
        post_data = {
            'title': fake.name(),
            'publish': True,
            'description': ' '.join(fake.sentences())
        }
        with open(file, 'rb') as image:
            post_data.update({'image': image})
            response = auth_client.post(f'{EndPoint.POST}/', data=post_data, format='multipart')
            assert response.status_code == 201

        # list post
        list_response = client.get(f'{EndPoint.POST}/?limit=3', format='json')
        assert list_response.status_code == 200
        results = list_response.data['data']['results']
        post_exist = list(filter(lambda x: x.get('title') == post_data['title'], results))
        assert len(post_exist) > 0

        # update post
        update_data = {
            'title': fake.sentence(),
            'description': post_exist[0]['description']
        }
        update_response = auth_client.put(f'{EndPoint.POST}/{post_exist[0]["id"]}/', data=update_data, format='json')
        assert update_response.status_code == 200
        update_results = update_response.data['data']
        assert update_data['title'] == update_results['title']

        # delete post
        delete_response = auth_client.delete(f'{EndPoint.POST}/{post_exist[0]["id"]}/', format='json')
        assert delete_response.status_code == 204

        # retrieve post
        retrieve_response = auth_client.get(f'{EndPoint.POST}/{post_exist[0]["id"]}/', format='json')
        assert retrieve_response.status_code == 400

    def test_post_comment_integration(self, client, auth_client):
        post_data = {
            'title': fake.name(),
            'publish': True,
            'description': ' '.join(fake.sentences())
        }
        with open(file, 'rb') as image:
            post_data.update({'image': image})
            response = auth_client.post(f'{EndPoint.POST}/', data=post_data, format='multipart')
            assert response.status_code == 201

        list_response = client.get(f'{EndPoint.POST}/?limit=3', format='json')
        assert list_response.status_code == 200
        results = list_response.data['data']['results']
        post_exist = list(filter(lambda x: x.get('title') == post_data['title'], results))
        assert len(post_exist) > 0
        # create a comment
        comment_load = {
            'post_id': post_exist[0]['id'],
            'body': fake.sentence()
        }
        comment_response = auth_client.post(f'{EndPoint.COMMENT}/', comment_load, 'json')
        assert comment_response.status_code == 201
        # list comments
        list_comments = client.get(f'{EndPoint.COMMENT}/?limit=3&post__id={comment_load["post_id"]}', format='json')
        assert list_response.status_code == 200
        list_comment_results = list_comments.data['data']['results']
        assert len(list_comment_results) > 0

        # create a reply to the already created comment
        comment_reply_load = {
            'parent_comment_id': list_comment_results[0]['id'],
            'body': fake.sentence()
        }
        comment_response = auth_client.post(f'{EndPoint.COMMENT}/', comment_reply_load, 'json')
        print(comment_response.data)
        assert comment_response.status_code == 201
        comment_reply_data = comment_response.data['data']
        assert comment_reply_data['body'] == comment_reply_load['body']

        # fetch comment replies
        replies_response = client.get(f'{EndPoint.COMMENT}/{list_comment_results[0]["id"]}/replies/',
                                      comment_reply_load, 'json')
        assert replies_response.status_code == 200
        reply_results = replies_response.data['data']
        assert len(reply_results) > 0
