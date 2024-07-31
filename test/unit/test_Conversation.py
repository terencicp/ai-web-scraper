import unittest
from helper import add_app_to_path

add_app_to_path(levels=3)
from app.ai.services.Conversation import Conversation
from app.ai.services.AnthropicRequest import AnthropicRequest
from app.ai.services.OpenAiRequest import OpenAiRequest
from app.ai.services.ModelRequest import ModelRequest
from app.ai.services.anthropic_models import Claude35Sonnet
from app.ai.services.openai_models import Gpt4o


class TestConversation(unittest.TestCase):

    def test_sonnet_image_format(self):
        # Checks that image objects match the expected format for the Anthropic API
        sonnet_request = AnthropicRequest(Claude35Sonnet())
        conversation = Conversation(sonnet_request)
        conversation.add_text("text")
        conversation.add_image("base64_image")
        formatted_messages = conversation._format_images()
        expected_formatted_image_message = {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": "base64_image"
            }
        }
        self.assertIn(expected_formatted_image_message, formatted_messages[0]["content"])

    def test_gpt4_image_format(self):
        # Checks that image objects match the expected format for the OpenAI API
        gpt4_request = OpenAiRequest(Gpt4o())
        conversation = Conversation(gpt4_request)
        conversation.add_text("text")
        conversation.add_image("base64_image")
        formatted_messages = conversation._format_images()
        expected_formatted_image_message = {
            "type": "image_url",
            "image_url": {
                "url": "data:image/png;base64,base64_image"
            }
        }
        self.assertIn(expected_formatted_image_message, formatted_messages[0]["content"])

    def test_reset(self):
        # Checks that model parameters and messages are reset
        model_request = AnthropicRequest(Claude35Sonnet(), max_tokens=1)
        conversation = Conversation(model_request)
        conversation.messages.append({"role": "user", "content": "Hello"})
        conversation.reset()
        # Check that messages are deleted
        self.assertEqual(len(conversation.messages), 0)

if __name__ == '__main__':
    unittest.main()
