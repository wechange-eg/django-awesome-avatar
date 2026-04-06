from io import BytesIO
from logging import getLogger

from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.exceptions import ValidationError
from django.utils.encoding import force_str

from PIL import Image

from awesome_avatar.settings import config
from awesome_avatar.widgets import AvatarWidget


logger = getLogger(__name__)

class AvatarField(forms.ImageField):
    widget = AvatarWidget

    def __init__(self, **defaults):
        self.width = defaults.pop('width', config.width)
        self.height = defaults.pop('height', config.height)
        self.disable_preview = defaults.pop('disable_preview', False)
        super(AvatarField, self).__init__(**defaults)

    @staticmethod
    def _sanitize_image_format(image: InMemoryUploadedFile) -> InMemoryUploadedFile:
        """
        Ensures, the image has a compatible data format.
        - converts to RGB jpeg, if image has an uncommon data format (CMYK, etc.)
        - raises ValidationError on Error
        """
        try:
            pil_img = Image.open(image)

            # return "common" modes unchanged,
            # see https://pillow.readthedocs.io/en/stable/handbook/concepts.html#concept-modes
            if pil_img.mode in ['1', 'L', 'P', 'RGB', 'RGBA']:
                return image

            # convert "uncommon" modes to RGB, save as JPEG
            pil_img = pil_img.convert('RGB')
            output_image = BytesIO()
            pil_img.save(output_image, format='JPEG', quality=90, optimize=True)
            # seek to start position for django to be able to read the data
            output_image.seek(0)

            result_image = InMemoryUploadedFile(file=output_image,
                                                field_name=image.field_name,
                                                name=image.name,
                                                content_type='image/jpeg',
                                                size=output_image.getbuffer().nbytes,
                                                charset=None)
            return result_image
        except Exception as e:
            logger.error('Error during image processing', extra={'exception': force_str(e)})
            raise ValidationError('Error during image processing. Please use a common Image format.')

    def to_python(self, data):
        super(AvatarField, self).to_python(getattr(data, 'file', None))
        return data
    
    def clean(self, data, initial=None):
        if not data and initial:
            return initial

        # make sure, the image is valid, raises ValidationError on failure
        data['file'] = self._sanitize_image_format(data['file'])

        return data

    def widget_attrs(self, widget):
        return {'width': self.width, 'height': self.height, 'disable_preview': self.disable_preview}