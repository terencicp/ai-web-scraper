import email
import json
import time
import requests
from typing import List, Optional, Dict
from requests.exceptions import RequestException

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager

from app.navigation.Document import Document
from app.navigation.Screenshot import Screenshot


class Browser:
    """ 
    Controls the Chrome browser and extracts content from websites. 

    Usage example:
        browser = Browser()
        browser.go_to_url('https://www.example.com')
        was_element_clicked = browser.click_element(By.ID, 'some_id')
        base64_string = browser.take_screenshot_as_base64()
        html_iframe_list = browser.get_embedded_html()
        browser.reload_page()
        browser.close()

    Requirements:
        Google Chrome installed.
    """

    SELECTOR_TYPES = {'id': By.ID, 'class': By.CLASS_NAME, 'xpath': By.XPATH}

    LOADING_TIME = 3

    def __init__(self) -> None:
        """ Initializes the Browser's driver and an empty Document."""
        self._driver: WebDriver = self._setup_chrome_driver()
        self.document: Document = None
    
    def _setup_chrome_driver(self) -> WebDriver:
        """ Installs, initializes and returns the Chrome driver. """
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_experimental_option("prefs", {"translate": {"enabled": False}})
        options.add_argument('--disable-translate')
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    
    def go_to_url(self, url: str) -> None:
        """ Go to the URL and wait for the page to load. """
        self._driver.get(url)
        time.sleep(self.LOADING_TIME)
        self.document = Document(self.get_main_html())

    def take_screenshot_as_base64(self) -> str:
        """ Screenshots of the current page as a base64 string. """
        png = self._driver.get_screenshot_as_png()
        return Screenshot(png).as_base64()

    def click_element(self, selector_type: str, selector: str) -> bool:
        """ Clicks page elements based on the given selector. """
        if selector_type not in self.SELECTOR_TYPES:
            return
        selector_type = self.SELECTOR_TYPES[selector_type]
        elements = self._find_and_click_elements(selector_type, selector)
        if not elements:
            for iframe in self._driver.find_elements(By.TAG_NAME, 'iframe'):
                self._driver.switch_to.frame(iframe)
                elements = self._find_and_click_elements(selector_type, selector)
                self._driver.switch_to.default_content()
        time.sleep(self.LOADING_TIME)
        self.document.update(self.get_main_html())
        return bool(elements)

    def _find_and_click_elements(self, selector_type: str, selector: str) -> List:
        elements = self._driver.find_elements(self.SELECTOR_TYPES[selector_type], selector)
        for element in elements:
            try:
                element.click()
            except (StaleElementReferenceException, ElementNotInteractableException):
                continue
        return elements

    def _post_request(self, url: str, body: str) -> Optional[Dict]:
        """ Sends a POST request to the URL and returns the response. """
        try:
            headers = {'Content-Type': 'application/json'}
            return requests.post(url, body, headers=headers, timeout=self.LOADING_TIME)
        except RequestException as error:
            return None

    def _take_page_snapshot(self) -> Optional[str]:
        """ Get the current page as an MHT string. """
        self._scoll_to_bottom()
        resource = f"/session/{self._driver.session_id}/chromium/send_command_and_get_result"
        url = self._driver.command_executor._url + resource
        body = json.dumps({'cmd': 'Page.captureSnapshot', 'params': {}})
        response = self._post_request(url, body)
        if response:
            return response.json().get('value').get('data')
        else:
            return None

    def _scoll_to_bottom(self) -> None:
        """ Scrolls to the bottom of the page to load all content. """
        body = self._driver.find_element(By.TAG_NAME, 'body')
        body.send_keys(Keys.END)
        time.sleep(self.LOADING_TIME)
        body.send_keys(Keys.HOME)

    def _extract_embedded_docs(self, mht: Optional[str]) -> List[str]:
        """ Extracts all HTML documents from an MHT string. """
        if mht is None:
            return []
        message = email.message_from_string(mht)
        html_documents = []
        for part in message.walk():
            if part.get_content_type() == 'text/html':
                html_documents.append(part.get_payload(decode=True).decode('utf-8'))
        return html_documents

    def get_main_html(self) -> List[str]:
        """ Get the main HTML document from the current page. """
        return [self._driver.page_source]

    def get_embedded_html(self) -> List[str]:
        """ Get all HTML documents inside <iframe> from the page. """
        page_snapshot = self._take_page_snapshot()
        embedded_docs = self._extract_embedded_docs(page_snapshot)
        return embedded_docs

    def reload_page(self) -> None:
        """ Reloads the current page and updates the document. """
        self._driver.refresh()
        time.sleep(self.LOADING_TIME)
        self.document.update(self.get_main_html())

    def get_url(self) -> str:
        """ Returns the current URL of the browser. """
        return self._driver.current_url

    def close(self) -> None:
        """ Close the browser. """
        self._driver.quit()