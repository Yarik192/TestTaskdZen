import os

from django.core.exceptions import ValidationError


def validate_image_extension(image):
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    ext = os.path.splitext(image.name)[1].lower()
    if ext not in valid_extensions:
        raise ValidationError("Допустимые форматы: JPG, JPEG, PNG, GIF")
