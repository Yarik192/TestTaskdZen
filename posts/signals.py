from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Post
from common.kafka_client import send_post_created_message
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Post)
def after_post_save(sender, instance, created, **kwargs):
    """Сигнал срабатывающий после сохранения поста"""
    if created:
        post_data = {
            "id": instance.id,
            "username": instance.username,
            "email": instance.email,
            "text": instance.text,
            "timestamp": instance.timestamp.isoformat() if instance.timestamp else None,
            "image": str(instance.image) if instance.image else None,
            "text_file": str(instance.text_file) if instance.text_file else None,
            "parent_post_id": instance.parent_post.id if instance.parent_post else None,
        }

        success = send_post_created_message(post_data)
        if success:
            logger.info(f"Сообщение о новом посте {instance.id} успешно отправлено в Kafka")
        else:
            logger.error(f"Ошибка отправки сообщения о посте {instance.id} в Kafka")