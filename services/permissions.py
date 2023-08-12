from functools import wraps
from rest_framework import status
from rest_framework.response import Response


def global_permission():
    """
    Grant global permission to users
    """

    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated is False:
                return Response(
                    {
                        "status": status.HTTP_401_UNAUTHORIZED,
                        "message": "You must be authenticated before accessing this resource",
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            response = func(request, *args, **kwargs)
            return response

        return wrapper

    return decorator
