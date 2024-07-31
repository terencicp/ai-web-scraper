import json
import random
from string import Template
from textwrap import dedent
from typing import Optional, List, Dict, Any

from app.ai.services.OpenAiRequest import OpenAiRequest
from app.ai.services.Conversation import Conversation
from app.ai.data.ScrapedData import ScrapedData
from app.ai.services.openai_models import Gpt4o 


class Validator:
    """
    Agent that checks if a JSON file contains the data the user requested.

    Usage example:
        validator = Validator()
        url = "https://www.example.com"
        file_name = "data0"
        user_intent = "List of countries and capitals"
        data_if_file_exists = validator.load_data_file(url, file_name)
        if not data_if_file_exists:
            print("Data could not be extracted from the current page.\n")
        is_data_valid = validator.validate(user_intent)
        if is_data_valid:
            return data_if_file_exists
        else:
            print(f"The data found is not valid. {self._validator.error}\n")
    """

    VALIDATE_JSON = Template(dedent("""
    The following represents a sample of an array of data scrapped from a website: $data_sample
    Note the actual JSON file contains $remaining_data_length more objects, I only showed you 2 for brevity.
    Check if the sampled JSON objects match the user query: $user_intent
    Do the objects contain enough information to answer the user's request?
    Return a valid JSON object with values:
    - data_description: A short description of the sampled objects with respect to the user's request.
    - is_valid: True if the data is related to the user's request and contains enough information, False otherwise.
    - error: If is_valid is False, a message explaining why the data is invalid. 
    Important: The data comes from a Google search, so in case of ambiguity, always assume it's relevant.
    Only consider the data invalid if it's completely unrelated to the user's request or
    if each object contains too few values to consider it a useful answer. False negatives are unacceptable.
    """))

    DATA_SAMPLE_SIZE = 2

    data: List[ScrapedData] = []

    def __init__(self) -> None:
        """ Initializes the Validator with a Conversation. """
        model_request = OpenAiRequest(Gpt4o(), json_response=True)
        self._conversation = Conversation(model_request)
        self.error: str

    def load_data_file(self, url: str, file_name: str) -> Optional[ScrapedData]:
        """ Adds a JSON file's content to the data list, returns False if empty or not found. """
        file_name = f'{file_name}.json'
        json_content = self._load_file_content(file_name)
        if json_content is None:
            return None
        data = ScrapedData(file_name, url, json_content)
        self.data.append(data)
        return data

    def _load_file_content(self, file_name: str):
        """ Loads the content of the given file and returns it, or None if there's an error. """
        try:
            with open(file_name, 'r', encoding='utf-8') as file:
                json_content = json.load(file)
            if not json_content:
                raise ValueError("File is empty")
            return json_content
        except (FileNotFoundError, ValueError) as e:
            self.error = f"Error with file {file_name}: {str(e)}"
            return None

    def validate(self, user_intent: str) -> Optional[bool]:
        """ Validates the data in a JSON file against the user query. """
        data_sample = self.get_data_item_sample(self.data[-1])
        answer = self._generate_validation(user_intent, data_sample)
        if answer:
            return self._is_json_valid(answer)
    
    @staticmethod
    def get_data_item_sample(item: ScrapedData) -> str:
        """ Returns a sample of a few objects in the given list. """
        if item.length <= Validator.DATA_SAMPLE_SIZE:
            return json.dumps(item.content)
        sample = random.sample(item.content, Validator.DATA_SAMPLE_SIZE)
        sample_with_ellipsis = json.dumps(sample)[:-2] + '}, ...]'
        return sample_with_ellipsis

    def _generate_validation(self, user_intent: str, data_sample: str) -> Optional[Dict[str, Any]]:
        """ Ask the LLM if the data sample matches the user query. """
        prompt = self._write_prompt(user_intent, data_sample)
        self._conversation.add_text(prompt)
        answer = self._conversation.request_answer()
        return answer
    
    def _write_prompt(self, user_intent: str, data_sample: str) -> str:
        """ Writes a prompt for the LLM to compare the data with the user's intent. """
        remaining_data_length = self.data[-1].length - self.DATA_SAMPLE_SIZE
        prompt = self.VALIDATE_JSON.substitute(
            data_sample = data_sample,
            remaining_data_length = remaining_data_length,
            user_intent = user_intent
        )
        return prompt
    
    def _is_json_valid(self, answer: Dict[str, Any]) -> bool:
        """ Parses the LLM's answer in response to a single JSON file. """
        if answer.get('is_valid'):
            return True
        else:
            self.error = answer.get('error')
            return False

    def _get_data_samples(self) -> str:
        """ Returns a sample of each item in the data list. """
        data_sample = ""
        for item in self.data:
            item_sample = self.get_data_item_sample(item)
            data_sample += f"{item.file_name}:\n{item_sample}\n\n"
        return data_sample