from PIL import Image
from django.db import models

from common.validators import validate_image_extension


class Post(models.Model):
    parent_post = models.OneToOneField("Post", on_delete=models.CASCADE, blank=True, null=True, related_name="child")
    username = models.CharField(max_length=64)
    email = models.EmailField()
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to="media/", null=True, blank=True, validators=[validate_image_extension])

    def __str__(self):
        return f"{self.username}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.image:
            img = Image.open(self.image.path)

            max_width, max_height = 320, 240

            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                img.save(self.image.path)

    class Meta:
        ordering = ['-timestamp']
