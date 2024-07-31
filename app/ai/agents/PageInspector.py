from typing import Tuple
from textwrap import dedent

from app.navigation.Browser import Browser
from app.ai.services.OpenAiRequest import OpenAiRequest
from app.ai.services.Conversation import Conversation
from app.ai.services.openai_models import Gpt4o

class PageInspector:
    """
    Agent that given a website's screenshot, checks if there were problems loading the web page
    and attemps to solve them or prompt the user to do so.

    Usage example:
        inspector = PageInspector(browser)
        loading_failed, issue = inspector.identify_loading_issues()
        if loading_failed:
            if issue == 'popup':
                print("Please close the popup.")
            elif issue == 'captcha':
                print("Please verify you are a human.")
    """

    IDENTIFY_LOADING_ISSUES = dedent("""
    The image contains a screenshot of a web page. 
    Return a valid JSON object with three boolean values:
    - error: True if the web page did not load correctly and needs to be reloaded.
    - captcha: True if the web page contains a human verification test (or if our IP is blocked by the host).
    - popup: True if the web page has a popup above the content that prevents interaction with the content.
    If the page contains a cookie or privacy popup, write the xpath selector of the 'Accept' button. Example:
    - selector: "//*[text()=\"Yes, that's fine\"]" 
    If there's a modal, an ad or a banner but it's not obstructing the content, return False for 'popup'.
    """)

    def __init__(self, browser: Browser) -> None:
        """ Creates a conversation. """
        self.browser: Browser = browser
        model_request = OpenAiRequest(Gpt4o(), max_tokens=500, json_response=True)
        self.conversation = Conversation(model_request)
        self.html_before: str

    def identify_loading_issues(self) -> Tuple[bool, str]:
        """ Returns True if the page content is not ready. """
        self.html_before = str(self.browser.document.html)
        screenshot = self.browser.take_screenshot_as_base64()
        self.conversation.add_text(self.IDENTIFY_LOADING_ISSUES)
        self.conversation.add_image(screenshot)
        answer = self.conversation.request_answer()
        return self._did_loading_fail(answer)

    def _did_loading_fail(self, answer: dict) -> Tuple[bool, str]:
        """ Processes the answer to determine if loading failed. """
        if answer.get('error'):
            self.browser.reload_page()
            return False, 'error'
        if answer.get('captcha'):
            return True, 'captcha'
        if answer.get('popup'):
            if 'text' in answer.get('selector', ''):
                print("🤖 Trying to close the popup...")
                is_popup_open = self._click_text_button(answer['selector'])
                return is_popup_open, 'popup'
            return True, 'popup'
        return False, 'no issues found'

    def _click_text_button(self, selector: str) -> bool:
        """ Clicks the html element in the selector and returns True if the page has changed. """
        elements_clicked = self.browser.click_element('xpath', selector)
        if not elements_clicked:
            spaced_selector = selector.replace("='", "=' ").replace("']", " ']")
            elements_clicked = self.browser.click_element('xpath', spaced_selector)
        if not elements_clicked:
            return True
        return not self._has_html_changed()

    def _has_html_changed(self) -> bool:
        """ Returns True if the html has changed. """
        html_after = str(self.browser.document.html)
        return bool(self.html_before != html_after)
