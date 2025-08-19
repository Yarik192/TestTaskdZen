from PIL import Image
from django.db import models

from common.validators import validate_image_extension, validate_text_file_size


class Post(models.Model):
    parent_post = models.OneToOneField("Post", on_delete=models.CASCADE, blank=True, null=True, related_name="child")
    username = models.CharField(max_length=64)
    email = models.EmailField()
    text = models.TextField()
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
        super().save(*args, **kwargs)

        if self.image:
            img = Image.open(self.image.path)

            max_width, max_height = 320, 240

            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                img.save(self.image.path)
