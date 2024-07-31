import unittest
import textwrap
from helper import add_app_to_path

add_app_to_path(levels=3)
from app.ai.services.ModelRequest import ModelRequest
from app.ai.services.AnthropicRequest import AnthropicRequest
from app.ai.services.anthropic_models import Claude35Sonnet


class TestModelRequest(unittest.TestCase):

    def test_extract_script(self):
        model_request = AnthropicRequest(Claude35Sonnet())
        # Test with valid Python code block
        valid_input = textwrap.dedent("""\
            Here's a Python script:
            ```python
            def hello_world():
                print("Hello, World!")
            ```
        """)
        expected_output = textwrap.dedent("""\
            def hello_world():
                print("Hello, World!")
        """)
        self.assertEqual(model_request.extract_script(valid_input), expected_output.strip())
        # Test with no code block
        no_code_block = "This is just plain text with no code block."
        self.assertEqual(model_request.extract_script(no_code_block), no_code_block)

if __name__ == '__main__':
    unittest.main()