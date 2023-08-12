import uuid

from rest_framework_simplejwt.tokens import RefreshToken


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


def generate_uuid(model, column):
    unique = str(uuid.uuid4())
    kwargs = {column: unique}
    qs_exists = model.objects.filter(**kwargs).exists()
    if qs_exists:
        return generate_uuid(model, column)
    return unique


def error_message_formatter(serializer_errors: dict):
    """Formats serializer error messages to dictionary"""
    return {f"{name}": f"{message[0]}" for name, message in serializer_errors.items()}


class CustomEnum(object):
    """
    Base Enum class in which all the enums configuration could inherit from.
    """

    class Enum(object):
        name = None
        value = None
        type = None

        def __init__(self, name, value, type):
            self.key = name
            self.name = name
            self.value = value
            self.type = type

        def __str__(self):
            return self.name

        def __repr__(self):
            return self.name

        def __eq__(self, other):
            if other is None:
                return False
            if isinstance(other, CustomEnum.Enum):
                return self.value == other.value
            raise TypeError

    @classmethod
    def choices(cls):
        """
        Methods return a tuple / list representation of the class attribute
        """
        attrs = [a for a in cls.__dict__.keys() if a.isupper()]
        values = [
            (cls.__dict__[v], CustomEnum.Enum(v, cls.__dict__[v], cls).__str__())
            for v in attrs
        ]
        return sorted(values, key=lambda x: x[0])
