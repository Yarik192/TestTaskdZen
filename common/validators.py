import os

from django.core.exceptions import ValidationError


def validate_image_extension(image):
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    ext = os.path.splitext(image.name)[1].lower()
    if ext not in valid_extensions:
        raise ValidationError("Допустимые форматы: JPG, JPEG, PNG, GIF")


def validate_text_file_size(value):
    limit_kb = 100
    if value.size > limit_kb * 1024:
        raise ValidationError(f"Размер файла не должен превышать {limit_kb} КБ.")
