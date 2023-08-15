import logging
from django.core.cache import cache
from django.dispatch import receiver
from django.db import models
from traceback_with_variables import format_exc

from core.models import Post

logger = logging.getLogger('core')


@receiver(models.signals.post_delete, sender=Post)
def auto_delete_image_on_change_user(sender, instance, **kwargs):
    try:
        cache.delete_many(keys=cache.keys('*.post.*'))
    except Exception as ex:
        logger.error(f'Something went wrong while deleting cache due to {str(ex)}')
        logger.error(format_exc(ex))
