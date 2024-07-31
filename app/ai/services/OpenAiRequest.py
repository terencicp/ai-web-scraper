from typing import List, Dict, Any, Optional

from openai import OpenAI

from app.ai.services.ModelRequest import ModelRequest
from app.ai.services.openai_models import OpenAiModel


class OpenAiRequest(ModelRequest):
    """
    Represents an OpenAI API Client request using using the specified model.

    Requirements:
        Environment variable 'OPENAI_API_KEY'.
    """

    ENVIRONMENT_VAR = 'OPENAI_API_KEY'

    def __init__(self,
        model: OpenAiModel,
        temperature: float = ModelRequest.TEMPERATURE,
        max_tokens: int = ModelRequest.MAX_TOKENS,
        json_response: bool = ModelRequest.JSON_RESPONSE,
        python_response: bool = ModelRequest.PYTHON_RESPONSE
    ) -> None:
        """ Sets the model parameters. Initializes the API client. """
        super().__init__(temperature, max_tokens, json_response, python_response)
        self.client = OpenAI()
        self.model = model

    def _send_request(self, messages: List[Dict[str, Any]]) -> Any:
        """ Sends the API request, setting JSON mode if required. """
        request_params = {
            "model": self.model.name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": messages
        }
        if self.json_response:
            request_params["response_format"] = {"type": "json_object"}
        return self.client.chat.completions.create(**request_params)

    def get_answer(self) -> Optional[str]:
        """ Extracts the answer's text from the API response. """
        if self.api_client_response and self.api_client_response.choices:
            answer = self.api_client_response.choices[0].message.content
            return answer
        return None

    @staticmethod
    def format_image(image: Dict[str, str]):
        """ Formats an image as URL as required by the OpenAI API. """
        return {
          "type": "image_url",
          "image_url": {
              "url": f"data:image/png;base64,{image["image"]}"
              }
        }
