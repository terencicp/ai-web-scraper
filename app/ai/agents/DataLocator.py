import itertools
import random
from typing import List, Optional, Dict, Any, Tuple, Union
from textwrap import dedent
from string import Template

from app.navigation.Browser import Browser
from app.ai.services.Conversation import Conversation
from app.ai.services.OpenAiRequest import OpenAiRequest
from app.navigation.ExtendedTag import ExtendedTag as Tag
from app.ai.data.DocumentData import DocumentData
from app.ai.data.DataType import DataType
from app.ai.utils.StringUtils import StringUtils
from app.ai.services.openai_models import Gpt4oMini 


class DataLocator:
    """
    Agent that locates data on a web page given a user query.

    Usage example:
        data_locator = DataLocator(browser)
        user_intent = "List of countries and capitals"
        file_name = "data0"
        data_location_attempt = 0
        while not data:
            if feedback:
                data_locator.set_feedback(feedback)
            data_sample, data_type = data_locator.find(user_intent, file_name, data_location_attempt)
            data_location_attempt += 1
            ...
    """

    GET_DATA_SAMPLE = Template(dedent("""
    Write a JSON array that contains the first data item, three in-between items, and last item the user requested.
    Make sure the last item is the bottomost item of relevant data and not the last item of the first section of the website.
    Copy the values literally from the website's text. Write valid JSON. Example:
    {"data": [{"country": "Austria", "capital": "Vienna", ...}, ..., {"country": "Sweden", "capital": "Stockholm", ...}]}
    Data should not have any value that's identical for all objects (no generic or null values allowed).
    If there's no relevant data in the website's text, return an empty array.
    Data requested by the user: $query
    Website's text (contains one html tag per line, long strings are truncated using ...): $text
    """))

    MAX_STRING_LENGTH = 100  # Max length of the strings in each html tag passed to the LLM
    MAX_TEXT_LENGTH = 50000  # Max length of the total text passed to the LLM

    def __init__(self, browser: Browser) -> None:
        """ Initializes the DataLocator with a Browser and a Conversation. """
        self._browser: Browser = browser
        self._model_request = OpenAiRequest(Gpt4oMini(), json_response=True)
        self._conversation = Conversation(self._model_request)
        self._sample_strings: List[str] = []
        self._feedback: Optional[str] = None

    def find(self, user_query: str, file_name: str, attempts: int) -> Tuple[Tag, DataType]:
        """ Locates and returns the HTML container of the requested data. """
        data = self._find_data(user_query, attempts > 0)
        if not data or not data.container:
            self._save_data(self._browser.document.body, file_name)
            return (self._browser.document.body, DataType.DATA_NOT_FOUND)
        if attempts > 1:
            return (data.container, DataType.CONTAINER)
        table = data.container.find_parent_table()
        if table:
            table_sample = table.get_first_rows(15)
            self._save_data(table, file_name)
            return (table_sample, DataType.TABLE)
        self._save_data(data.container, file_name)
        first_item = self._find_first_item(data)
        if first_item:
            if first_item.is_text_tag():
                return (data.container, DataType.TEXT)
            else:
                return (first_item, DataType.FIRST_ITEM)
        distinct_children = self._remove_similar_children(data.container)
        return (distinct_children, DataType.DISTINCT_ITEMS)
    
    def set_feedback(self, feedback: str) -> None:
        """ Sets the feedback for the data locator. """
        self._feedback = feedback

    def _save_data(self, data: Tag, file_name: str) -> None:
        """ Saves the data as an HTML file. """
        with open(f'{file_name}.html', 'w', encoding='utf-8') as file:
            file.write(str(data))

    def _find_data(self, user_query: str, not_first_attempt: bool) -> Optional[DocumentData]:
        """ Locates and returns the HTML container of the requested data. """
        if not_first_attempt:
            self._conversation.reset()
        data = self._find_data_structure(user_query)
        if not data:
            embedded_docs = self._browser.get_embedded_html()
            if not embedded_docs:
                return None
            self._browser.document.update(embedded_docs)
            data = self._find_data_structure(user_query)
        return data

    def _find_data_structure(self, user_query: str) -> DocumentData:
        """ Locates and returns the HTML container of the requested data. """
        sample_data = self._generate_data_sample(user_query)
        if not sample_data:
            return None
        self._sample_strings = self._extract_sample_strings(sample_data)
        data_elements1 = self._find_data_elements(sample_data[0])
        data_elements2 = self._find_data_elements(sample_data[-1])
        if not data_elements1 or not data_elements2:
            return None
        data_container_and_elements = self._find_data_container(data_elements1, data_elements2)
        return data_container_and_elements

    def _generate_data_sample(self, user_query: str) -> Optional[List[Dict]]:
        """ Requests sample data from the model based on the user query and page text. """
        if not self._browser.document.body:
            self._browser.document.update(self._browser.get_main_html())
        page_text = self._browser.document.get_text(self.MAX_STRING_LENGTH)
        page_text = StringUtils.split_with_ellipsis(page_text, self.MAX_TEXT_LENGTH)
        prompt = self.GET_DATA_SAMPLE.substitute(query=user_query, text=page_text)
        if self._feedback:
            prompt += f"\nUser feedback from the previous data location attempt: {self._feedback}"
        self._conversation.add_text(prompt)
        answer = self._conversation.request_answer()
        if answer and 'data' in answer and len(answer['data']) > 1:
            return answer['data']
        return None

    def _extract_sample_strings(self, sample_data: List[Dict[str, Any]]) -> List[str]:
        """ Extracts values from dictionaries as strings. """
        sample_strings = []
        for item in sample_data:
            sample_strings.extend(self._extract_values(item))
        return sample_strings

    def _find_data_elements(self, sample_data: Dict[str, Any]) -> List[Tag]:
        """ Finds and returns the HTML elements that contain the sample data. """
        sample_strings = self._extract_values(sample_data)
        sample_strings = [s.rstrip('.') if s.endswith('...') else s for s in sample_strings]
        self._sample_strings = self._sample_strings + sample_strings
        data_elements = []
        for string in sample_strings:
            new_data_elements = self._browser.document.find_elements_by_text(string)
            if new_data_elements:
                data_elements.extend(new_data_elements)
        return data_elements
    
    def _extract_values(self, item: Union[List, Dict]) -> List[str]:
        """ Recursively extracts a list of strings from a JSON object. """
        if isinstance(item, (str, int, float)): # Ignores booleans
            return [str(item)]
        elif isinstance(item, dict):
            return [s for v in item.values() for s in self._extract_values(v)]
        elif isinstance(item, list):
            return [s for v in item for s in self._extract_values(v)]
        else:
            return []
    
    def _find_data_container(self, data_elements1, data_elements2) -> DocumentData:
        """ Finds and returns the data container and elements used to find it. """
        element_pairs = self._pairs(data_elements1, data_elements2)
        if len(element_pairs) > 1000:
            element_pairs = random.sample(element_pairs, 1000)
        data = []
        for element1, element2 in element_pairs:
            container = self._browser.document.find_common_ancestor(element1, element2)
            data.append(DocumentData(container, element1, element2))
        data = self._filter_unique_containers(data)
        if len(data) == 1:
            return data[0]
        data = self._filter_data(data)
        if len(data) == 1:
            return data[0]
        data = self._filter_wrappers(data)
        if not data:
            return DocumentData()
        return max(data, key=lambda data: data.proportion)

    def _pairs(self, list_a: List, list_b: List) -> List[Tuple]:
        """ Returns all combinations of two distinct elements. """
        return list(itertools.product(list_a, list_b))

    def _filter_unique_containers(self, data: List[DocumentData]) -> List[DocumentData]:
        """ Filters out duplicate containers from the data. """
        return list({d.container: d for d in data}.values())
    
    def _filter_data(self, data: List[DocumentData]) -> List[DocumentData]:
        """ Filters data based on the proportion of sample text found in each container. """
        filtered_data = []
        for item in data:
            container_text = item.container.get_text().lower()
            strings_found = sum(string.lower() in container_text for string in self._sample_strings)
            item.proportion = strings_found / len(self._sample_strings)
            if item.proportion > 0.35:
                filtered_data.append(item)
        return filtered_data

    def _filter_wrappers(self, data: List[DocumentData]) -> List[DocumentData]:
        """ Filters out data with containers that are wrappers of the other containers. """
        filtered_data = []
        for data_a in data:
            if not any(data_b.container.is_descendant_of(data_a.container)
                    for data_b in data if data_a.proportion == data_b.proportion and data_a != data_b):
                filtered_data.append(data_a)
        return filtered_data

    def _find_first_item(self, data: DocumentData) -> Optional[Tag]:
        """ Returns the first child of the container (with data), if it has identical siblings. """
        ancestors1 = self._browser.document.find_ancestors(data.element1, data.container)
        ancestors2 = self._browser.document.find_ancestors(data.element2, data.container)
        if ancestors1[0].is_identical_to(ancestors2[0]):
            return ancestors1[0]
        else:
            return None

    def _remove_similar_children(self, container: Tag) -> Tag:
        """ Removes children with the same name and attributes from the container. """
        container = container.copy()
        name = container.name
        attributes = container.attrs
        pruned_container = self._browser.document.html.new_tag(name, **attributes)
        container.remove_children_style()
        distinct_children = self._browser.document.find_distinct_children(container)
        for child in distinct_children:
            pruned_container.append(child.copy())
        return pruned_container