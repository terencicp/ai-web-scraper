import json
from copy import deepcopy
import traceback
from typing import List, Dict, Any, Union

import tiktoken

from app.ai.services.ModelRequest import ModelRequest


class Conversation:
    """
    Represents messages in a conversation between the app and an LLM.

    Messages are stored in this format:
    [
        { "role": "user", "content": [
            { "type": "text", "text": "Say ELEPHANT" }
            { "type": "image", "image": "iVBORw0KGgoAAAA..." }
        ]}
        { "role": "assistant", "content": [
            { "type": "text", "text": "ELEPHANT" }
        ]}
    ]

    Usage example:
        conversation = Conversation()
        conversation.add_text("Cat breeds")
        conversation.add_image("base64_string")
        answer = conversation.request_answer("Validator")
    """

    total_cost = 0

    def __init__(self, model_request: ModelRequest) -> None:
        """ Initializes: LLM Client, message list, and a bool indicating if the API failed. """
        self.model_request = model_request
        self.messages: List[Dict[str, Any]] = []
        self.tokenizer = tiktoken.encoding_for_model('gpt-4o')

    def _add_message(self, role: str, content: Dict[str, Any]) -> None:
        """ Adds a message to the list under the specified role ('user' or 'assistant'). """
        self.messages.append({"role": role, "content": [content]})

    def add_text(self, text: str) -> None:
        """ Adds a text message to the list under the 'user' role. """
        self._add_message("user", {"type": "text", "text": str(text)})

    def add_image(self, base64: str) -> None:
        """ Adds an image to the last 'user' message. """
        if self.messages[-1]["role"] != "user":
            raise ValueError("Can't add image: last message is not from user")
        else:
            self.messages[-1]["content"].append({"type": "image", "image": base64})

    def replace_first_message(self, text: str) -> None:
        """ Replaces the first conversation message with the given text. """
        self.messages[0] = {"role": "user", "content": [{"type": "text", "text": str(text)}]}

    def request_answer(self) -> Union[None, Dict[str, Any], str]:
        """ Sends an API request and stores the response in messages. """
        try:
            self._add_input_cost()
            messages = self._format_images()
            self.model_request.send(messages)
            response = self.model_request.get_answer()
            self._add_output_cost(response)
            if response:
                self._add_message("assistant", {"type": "text", "text": response})
                return self._get_answer()
        except Exception as e:
            print(f"LLM API error: {str(e)}")
            print(traceback.format_exc())
            return None

    def _format_images(self) -> List[Dict[str, Any]]:
        """ Formats images in messages for the current API. """
        messages = deepcopy(self.messages)
        for message in messages:
            for i, content in enumerate(message["content"]):
                if content["type"] == "image":
                    message["content"][i] = self.model_request.format_image(content)
        return messages
                
    def _get_answer(self) -> Union[Dict[str, Any], str]:
        """ Returns the LLM answer as plain text or a dictionary. """
        text_answer = self.messages[-1]["content"][0]["text"]
        if self.model_request.json_response:
            json_answer = json.loads(text_answer)
            return json_answer
        elif self.model_request.python_response:
            script = ModelRequest.extract_script(text_answer)
            return script
        else:
            return text_answer

    def _add_input_cost(self) -> None:
        """ Adds an estimation of the cost of the messages sent to the total cost. """
        for message in self.messages:
            for content in message['content']:
                if content['type'] == 'text':
                    input_tokens = len(self.tokenizer.encode(content['text']))
                    Conversation.total_cost += input_tokens * self.model_request.model.input_token_cost
                elif content['type'] == 'image':
                    Conversation.total_cost += self.model_request.model.image_cost

    def _add_output_cost(self, response: str) -> None:
        """ Adds an estimation of the cost of the message received to the total cost. """
        output_tokens = len(self.tokenizer.encode(response))
        output_cost = output_tokens * self.model_request.model.output_token_cost
        Conversation.total_cost += output_cost

    def reset(self) -> None:
        """ Deletes messages and resets model parameters. """
        self.messages.clear()

    def __str__(self):
        """ Shows the text messages in the conversation. """
        output = []
        for message in self.messages:
            role = message['role']
            for content in message['content']:
                if content['type'] == 'text':
                    output.append(f"{role}: {content['text']}")
        return "\n".join(output)