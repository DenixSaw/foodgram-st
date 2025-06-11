import base64
import uuid

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers


class Binary64ImageField(Base64ImageField):
    def to_internal_value(self, data):
        if hasattr(data, 'file') and hasattr(data.file, 'read'):
            return data

        if isinstance(data, str):
            if data.startswith('data:image'):
                try:
                    format, imgstr = data.split(';base64,')
                    ext = format.split('/')[-1]

                    # Генерируем уникальное имя файла
                    file_name = f"{uuid.uuid4()}.{ext}"

                    # Декодируем и создаем ContentFile
                    decoded_file = base64.b64decode(imgstr)
                    return ContentFile(decoded_file, name=file_name)
                except (ValueError, AttributeError, TypeError):
                    raise serializers.ValidationError("Некорректный формат base64 строки")
            else:
                raise serializers.ValidationError("Это не base64 строка изображения")

        raise serializers.ValidationError("Некорректный тип данных. Ожидается base64 строка или файл")

    def to_representation(self, value):
        if not value:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(value.url)
        return value.url
