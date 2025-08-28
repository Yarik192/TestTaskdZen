from PIL import Image
from django.db import models
import logging

from common.validators import validate_image_extension, validate_text_file_size

logger = logging.getLogger(__name__)


class Post(models.Model):
    parent_post = models.OneToOneField("Post", on_delete=models.CASCADE, blank=True, null=True, related_name="child")
    username = models.CharField(max_length=64)
    email = models.EmailField()
    text = models.TextField(help_text="Текст поста (обязательное поле)")
    timestamp = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(null=True, blank=True, validators=[validate_image_extension])
    text_file = models.FileField(
        upload_to="text_files/",
        null=True,
        blank=True,
        validators=[validate_text_file_size],
    )

    def __str__(self):
        return f"{self.username}"

    def save(self, *args, **kwargs):
        if not self.text or not self.text.strip():
            raise ValueError("Текст поста не может быть пустым")
        
        super().save(*args, **kwargs)

        if self.image:
            img = Image.open(self.image.path)

            max_width, max_height = 320, 240

            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                img.save(self.image.path)
        
        try:
            from .search_service import post_search_service
            post_search_service.index_post(self)
        except Exception as e:
            logger.error(f"Ошибка индексации поста {self.id} в Elasticsearch: {e}")
    
    def delete(self, *args, **kwargs):
        try:
            from .search_service import post_search_service
            post_search_service.remove_post(self.id)
        except Exception as e:
            logger.error(f"Ошибка удаления поста {self.id} из Elasticsearch: {e}")
        
        super().delete(*args, **kwargs)