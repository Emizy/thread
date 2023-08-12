from django.db.models import Q

from core.models import User


class CustomAuthBackend(object):
    def authenticate(self, request, username=None, password=None):
        try:
            users = User.objects.filter(Q(email=username) | Q(username=username))
            for user in users:
                if user.check_password(password):
                    return user
            return None
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
