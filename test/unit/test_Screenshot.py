import unittest
from PIL import Image
import io
import base64
from helper import add_app_to_path

add_app_to_path(levels=3)
from app.navigation.Screenshot import Screenshot


class TestScreenshot(unittest.TestCase):

    def setUp(self):
        # Create a small red square PNG image for testing
        img = Image.new('RGB', (50, 50), color = (73, 109, 137))
        byte_arr = io.BytesIO()
        img.save(byte_arr, format='PNG')
        self.png_data = byte_arr.getvalue()

    def test_init(self):
        # Create a Screenshot object from PNG data
        screenshot = Screenshot(self.png_data)
        self.assertEqual(screenshot.image.format, 'PNG')

    def test_reduce_image_size(self):
        # Reduce the size of the image to 25x25 pixels
        screenshot = Screenshot(self.png_data)
        screenshot.max_height = 25  # Force size reduction
        screenshot.reduce_image_size()
        self.assertEqual(screenshot.image.height, 25)
        self.assertEqual(screenshot.image.width, 25)

    def test_as_base64(self):
        # Encode the PNG data as base64
        screenshot = Screenshot(self.png_data)
        base64_str = screenshot.as_base64()
        # Decode the base64 string back to bytes and compare with original
        decoded = base64.b64decode(base64_str)
        self.assertEqual(decoded, self.png_data)

if __name__ == '__main__':
    unittest.main()