from services.utility import CustomEnum
from django.conf import settings


class EndPoint(CustomEnum):
    """
    Enum class to hold all the endpoints available on the system
    """
    REGISTER = f'{settings.BASE_URL}/api/v1/auth/register/'
    LOGIN = f'{settings.BASE_URL}/api/v1/auth/login/'
    POST = f'{settings.BASE_URL}/api/v1/post'
    COMMENT = f'{settings.BASE_URL}/api/v1/post/comment'
