import uuid


def generate_uuid(model, column):
    unique = str(uuid.uuid4())
    kwargs = {column: unique}
    qs_exists = model.objects.filter(**kwargs).exists()
    if qs_exists:
        return generate_uuid(model, column)
    return unique
