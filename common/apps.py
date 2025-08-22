from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "common"
    
    def ready(self):
        try:
            from .kafka_client import kafka_producer
            if kafka_producer.producer:
                print("✅ Kafka producer успешно инициализирован")
            else:
                print("⚠️ Kafka producer не удалось инициализировать")
                
        except Exception as e:
            print(f"❌ Ошибка инициализации Kafka: {e}")
