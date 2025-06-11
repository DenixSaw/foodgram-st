import base64

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from drf_extra_fields.fields import Base64ImageField


class Binary64ImageField(Base64ImageField):
    def to_representation(self, value):
        if not value:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(value.url)

    def to_internal_value(self, data):
        if hasattr(data, 'file') and hasattr(data.file, 'read'):
            return data

        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr),
                name=f'avatar.{ext}'
            )

        return super().to_internal_value(data)