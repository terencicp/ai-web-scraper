import re # pylint: disable=unused-import
import os # pylint: disable=unused-import
import json
import sys
from io import StringIO
import traceback
from string import Template
from textwrap import dedent
from typing import Dict, Optional

from bs4 import BeautifulSoup # pylint: disable=unused-import

from app.ai.services.AnthropicRequest import AnthropicRequest
from app.ai.services.Conversation import Conversation
from app.ai.data.DataType import DataType
from app.navigation.ExtendedTag import ExtendedTag as Tag
from app.ai.data.ScrapedData import ScrapedData
from app.ai.data.FeedbackData import FeedbackData
from app.ai.utils.StringUtils import StringUtils
from app.ai.services.anthropic_models import Claude35Sonnet


class WebScraper:
    """
    Agent that writes a web scraping script to extract the data.

    Usage example:
        web_scraper = WebScraper()
        data_sample = Tag("<table><tr><td>...</td></tr></table>")
        scraped_data = ScrapedData(file_name, url, content)
        data_type = DataType.TABLE
        file_name = "data0"
        user_intent = "List of countries and capitals"
        web_scraper.set_source(scraped_data, data_type)
        if feedback:
            web_scraper.set_feedback(scraped_data, feedback)
        web_scraper.scrape(user_intent, file_name)
    """

    WRITE_SCRIPT = Template(dedent("""
    Write a web scraper to extract the data the user requested from $file_name.html
    using BeautifulSoup and save it as $file_name.json. Extract as much data as possible.
    The resulting JSON should be an array of objects with the same keys.
    Before writing the script, briefly describe your strategy:
        1. Locate the data in the HTML that best matches the user's request
        2. List the keys the resulting JSON will contain
        3. For each key describe the tags and attributes needed to extract the data
        4. How you will clean the data?
        5. How will you handle missing data and errors?
    Your answer should include a single valid python code block without comments.
    Load the data using: "with open('$file_name.html', 'r') as file: html = file.read()"
    Include print statements to help debug the script in case something goes wrong.
    $user_intent
    """))

    REWRITE_SCRIPT1 = Template("The data extracted by the script doesn't meet the users expectations. Script output: $script_output")
    REWRITE_SCRIPT2 = Template("Sample of two data items (the actual JSON file has $data_length objects): $data_sample")
    REWRITE_SCRIPT3 = Template("User feedback: $feedback")

    DATA_DESCRIPTION_INTRO = "The following is a small sample from the html file. It contains "
    TABLE_SAMPLE = "the first rows of the table that contains the data:"
    FIRST_ITEM = "the first data element, assume others exist with the same structure:"
    DISTINCT_ITEMS = "a sample of elements that contain data, assume others exist with similar structures:"
    DEFAULT = "only elements that contain data:"

    MAX_HTML_LENGTH = 50000
    MAX_OUTPUT_LENGTH = 5000
    MAX_RETRIES = 2

    TAGS_TO_REMOVE = ['link', 'script', 'style', 'meta']
    ATTRIBUTES_TO_STRIP = [
        'lang', 'dir', 'style', 'width', 'height', 'rel', 'target', 'tabindex', 'frameborder', 'marginheight',
        'marginwidth', 'decoding', 'sizes', 'srcset', 'referrerpolicy', 'dir', 'playsinline', 'is-empty',
        'data-file-height', 'data-file-width', 'viewBox'
    ]

    def __init__(self) -> None:
        """ Creates a conversation and initializes variables. """
        self.model_request = AnthropicRequest(Claude35Sonnet(), python_response=True)
        self.conversation = Conversation(self.model_request)
        self.html_sample: str
        self.html_sample_type: DataType
        self._feedback: Optional[Dict] = None
        self._script_output = ""

    def set_source(self, html: Tag, data_type: DataType) -> None:
        """ Set the html sample to be fed to the LLM. """
        self.html_sample = self.clean_html(html)
        self.html_sample_type: DataType = data_type

    def clean_html(self, html: Tag) -> str:
        """ Remove HTML elements irrelevant for web scraping. """
        html = html.shorten_text(100)
        html = html.remove_comments()
        html = html.remove_tags(self.TAGS_TO_REMOVE)
        html = html.clear_svg_contents()
        html = html.strip_attributes(self.ATTRIBUTES_TO_STRIP)
        html = html.shorten_src(50)
        html = html.minify()
        html = StringUtils.trim_with_ellipsis(html, self.MAX_HTML_LENGTH)
        return html

    def set_feedback(self, data: Optional[ScrapedData], description: Optional[str]) -> None:
        """ Set feedback from the Validator or the user to retry scraping. """
        self._feedback = FeedbackData(data, description)

    def scrape(self, user_intent: str, file_name: str) -> None:
        """ Generate a web scraping script and run it. """
        file_name = f'{file_name}'
        script = self._generate_script(user_intent, file_name)
        error = self._run_script(script, file_name)
        retries = 0
        while error and retries < self.MAX_RETRIES:
            script = self._regenerate_script()
            error = self._run_script(script, file_name)
            retries += 1
            
    def _generate_script(self, user_intent: str, file_name: str) -> str:
        """ Generate a web scraping script based on a prompt. """
        prompt = self._write_prompt(user_intent, file_name)
        if not self._feedback:
            self.conversation.add_text(prompt)
        else:
            self.conversation.replace_first_message(prompt)
            feedback = self._rewrite_prompt()
            self.conversation.add_text(feedback)
        return self.conversation.request_answer()

    def _regenerate_script(self) -> str:
        """ Generate a web scraping script based on an error message. """
        self.conversation.add_text(self._script_output)
        return self.conversation.request_answer()

    def _write_prompt(self, user_intent: str, file_name: int) -> str:
        """ Writes the initial prompt for the LLM. """
        prompt = self.WRITE_SCRIPT.substitute(user_intent=user_intent, file_name=file_name)
        data_description = self._get_data_description()
        prompt += data_description
        if len(self.html_sample) > self.MAX_HTML_LENGTH:
            prompt += "\n" + "The complete html is too long and has been truncated."
        prompt += "\n" + self.html_sample
        return prompt.strip()

    def _rewrite_prompt(self) -> str:
        """ Writes the prompt to rewrite the script based on feedback. """
        prompt = self.REWRITE_SCRIPT1.substitute(
            script_output=self._script_output,
        )
        if self._feedback.data_length:
            prompt += self.REWRITE_SCRIPT2.substitute(
                data_sample=self._feedback.sample,
                data_length=self._feedback.data_length
            )
        if self._feedback.description:
            prompt += self.REWRITE_SCRIPT3.substitute(
                feedback=self._feedback.description
            )
        return prompt.strip()

    def _get_data_description(self) -> str:
        """ Returns a description of the data in the html sample. """
        descriptions = {
            DataType.TABLE: self.TABLE_SAMPLE,
            DataType.FIRST_ITEM: self.FIRST_ITEM,
            DataType.DISTINCT_ITEMS: self.DISTINCT_ITEMS
        }
        data_description_type = descriptions.get(self.html_sample_type, self.DEFAULT)
        return self.DATA_DESCRIPTION_INTRO + data_description_type

    def _run_script(self, script: str, file_name: str) -> bool:
        """ Run script, capture print output, check the output file exists. """
        captured_output = StringIO()
        sys_stdout = sys.stdout
        try:
            sys.stdout = captured_output
            exec(script) # pylint: disable=exec-used
            with open(f'{file_name}.json', 'r', encoding='utf-8') as file:
                json.load(file)
            self._script_output = captured_output.getvalue()
            return False
        except Exception: # pylint: disable=broad-exception-caught
            self._script_output = f"Rewrite the script: \n{traceback.format_exc()}"
            return True
        finally:
            sys.stdout = sys_stdout
            captured_output.close()
            self._limit_output_length()

    def _limit_output_length(self) -> None:
        """ Limit the length of the script output. """
        if len(self._script_output) > self.MAX_OUTPUT_LENGTH:
            self._script_output = self._script_output[:self.MAX_OUTPUT_LENGTH] + ' ...'
