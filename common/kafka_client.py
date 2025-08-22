import json
import logging
from typing import Dict, Any
from kafka import KafkaProducer
from django.conf import settings

logger = logging.getLogger(__name__)


class KafkaMessageProducer:
    def __init__(self):
        self.producer = None
        self._init_producer()
    
    def _init_producer(self):
        try:
            kafka_config = getattr(settings, "KAFKA_CONFIG", {})
            bootstrap_servers = kafka_config.get("bootstrap_servers", ["localhost:9092"])
            
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                retries=3,
                acks="all"
            )
            logger.info("Kafka producer успешно инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации Kafka producer: {e}")
            self.producer = None
    
    def send_message(self, topic: str, message: Dict[str, Any], key: str = None) -> bool:
        """
        Отправка сообщения в Kafka
        
        Args:
            topic: Топик Kafka
            message: Сообщение для отправки
            key: Ключ сообщения (опционально)
            
        Returns:
            bool: отправлено или нет
        """
        if not self.producer:
            logger.error("Kafka producer не инициализирован")
            return False
        
        try:
            future = self.producer.send(topic, value=message, key=key)
            record_metadata = future.get(timeout=10)
            logger.info(
                f"Сообщение отправлено в Kafka: topic={record_metadata.topic}, "
                f"partition={record_metadata.partition}, offset={record_metadata.offset}"
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения в Kafka: {e}")
            return False
    
    def close(self):
        if self.producer:
            self.producer.close()
            logger.info("Kafka producer закрыт")


kafka_producer = KafkaMessageProducer()


def send_post_created_message(post_data: Dict[str, Any]) -> bool:
    """
    Отправка сообщения о созданном посте в Kafka
    
    Args:
        post_data: Данные поста

    Returns:
        bool: True если сообщение отправлено успешно
    """
    topic = getattr(settings, "KAFKA_POSTS_TOPIC", "posts")
    
    message = {
        "event_type": "post_created",
        "post_id": post_data.get("id"),
        "username": post_data.get("username"),
        "email": post_data.get("email"),
        "text": post_data.get("text"),
        "timestamp": post_data.get("timestamp"),
        "has_image": bool(post_data.get("image")),
        "has_text_file": bool(post_data.get("text_file")),
        "parent_post_id": post_data.get("parent_post_id")
    }
    
    return kafka_producer.send_message(topic, message, key=str(post_data.get("id")))
