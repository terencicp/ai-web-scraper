import base64
from PIL import Image
import io
from typing import Union


class Screenshot:
    """ Represents an image, with methods to manipulate it. """

    max_height = 1200

    def __init__(self, png: bytes) -> None:
        """ Initialize the image from raw PNG data. """
        self.image: Image = Image.open(io.BytesIO(png))
        if self.image.height > self.max_height:
            self.reduce_image_size()

    def reduce_image_size(self) -> None:
        """ Halve the image if larger than the maximum height. """
        new_width = self.image.width // 2
        new_height = self.image.height // 2
        self.image = self.image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def as_base64(self) -> str:
        """ Returns the image as a base64 string. """
        buffered = io.BytesIO()
        self.image.save(buffered, format='PNG')
        img_str = base64.b64encode(buffered.getvalue())
        return img_str.decode('ascii')
    