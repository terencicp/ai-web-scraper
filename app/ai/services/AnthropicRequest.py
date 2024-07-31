from typing import List, Dict, Any, Optional

from anthropic import Anthropic
from anthropic.types.message import Message

from app.ai.services.ModelRequest import ModelRequest
from app.ai.services.anthropic_models import AnthropicModel


class AnthropicRequest(ModelRequest):
    """
    Represents an Anthropic API Client request using the specified model.

    Requirements:
        Environment variable 'ANTHROPIC_API_KEY'.
    """

    ENVIRONMENT_VAR = 'ANTHROPIC_API_KEY'

    def __init__(self,
        model: AnthropicModel,
        temperature: float = ModelRequest.TEMPERATURE,
        max_tokens: int = ModelRequest.MAX_TOKENS,
        json_response: bool = ModelRequest.JSON_RESPONSE,
        python_response: bool = ModelRequest.PYTHON_RESPONSE
    ) -> None:
        """ Sets the model parameters. Initializes the API client. """
        super().__init__(temperature, max_tokens, json_response, python_response)
        self.client = Anthropic()
        self.model = model

    def _send_request(self, messages: List[Dict[str, Any]]) -> Message:
        """ Sends the API request, prefilling the assistant's response if JSON is required. """
        if self.json_response and messages[-1]["role"] != "assistant":
            messages.append({
                "role": "assistant",
                "content": "JSON:\n{"  # Opening { will be missing in the answer
            })
        return self.client.messages.create(
            model=self.model.name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            messages=messages
        )

    def get_answer(self) -> Optional[str]:
        """ Extracts the answer's text from the API response, adding the missing { if it's JSON. """
        if self.api_client_response:
            answer = self.api_client_response.content[0].text
            if self.json_response:
                json_end = answer.rfind("}") + 1
                answer = "{" + answer[:json_end]
            return answer
        else:
            return None

    @staticmethod
    def format_image(image: Dict[str, str]):
        """ Formats an image as required by the Anthropic API. """
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": image["image"]
            }
        }
