from abc import ABC, abstractmethod
import os
from typing import List, Dict, Any, Optional
import re

class ModelRequest(ABC):
    """
    Represents an LLM API client request.

    Usage example:
        ...
    """
    
    ENVIRONMENT_VAR = ""
    TEMPERATURE = 0.7
    MAX_TOKENS = 4096
    JSON_RESPONSE = False
    PYTHON_RESPONSE = False

    def __init__(self,
        temperature: float = TEMPERATURE,
        max_tokens: int = MAX_TOKENS,
        json_response: bool = JSON_RESPONSE,
        python_response: bool = PYTHON_RESPONSE
    ) -> None:
        """ Sets the model parameters. Initializes a response object. """
        if not os.getenv(self.ENVIRONMENT_VAR):
            raise EnvironmentError(f"Please set the environment variable '{self.ENVIRONMENT_VAR}'.")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.json_response = json_response
        self.python_response = python_response
        self.api_client_response: Optional[Any] = None

    def send(self, messages: List[Dict[str, Any]]) -> None:
        """ Catches exceptions in the API request. """
        try:
            self.api_client_response = self._send_request(messages)
        except Exception as e:
            self.api_client_response = None
            raise ValueError(str(e)) from e

    @abstractmethod
    def _send_request(self, messages: List[Dict[str, Any]]) -> Any:
        """ Sends the API request. """

    @abstractmethod
    def get_answer(self) -> Optional[str]:
        """ Extracts the answer's text from the API response. """
    
    @staticmethod
    @abstractmethod
    def format_image(image: Dict[str, str]) -> Any:
        """ Formats an image for the API request. """

    @staticmethod
    def extract_script(answer: str) -> str:
        """ Extracts and validates the first python code block from a string. """
        match = re.search(r'```python(.*?)```', answer, re.DOTALL)
        script = match.group(1).strip() if match else answer
        return script