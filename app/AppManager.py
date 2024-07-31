from typing import Tuple, List, Optional

from app.search.Search import Search
from app.navigation.Browser import Browser
from app.ai.agents.UserQueryRewriter import UserQueryRewriter
from app.ai.agents.PageInspector import PageInspector
from app.ai.agents.DataLocator import DataLocator
from app.ai.agents.WebScraper import WebScraper
from app.ai.agents.Validator import Validator
from app.ai.data.ScrapedData import ScrapedData
from app.navigation.FileManager import FileManager
from app.ai.services.Conversation import Conversation


class AppManager:
    """ Main class that puts the different components together. """

    MAX_USER_VALIDATIONS_PER_WEBSITE = 3

    def __init__(self):
        self._search = Search()
        self._browser = None
        self._user_query_rewriter = UserQueryRewriter()
        self._page_inspector = None
        self._data_locator = None
        self._web_scraper = WebScraper()
        self._validator = Validator()
        self._file_manager = FileManager()
        self._file_index = 0
        self._scraping_attempts = 0
        self._feedback: Optional[str] = None
        self._data: Optional[ScrapedData] = None
        self._validator_failed = False

    def show_welcome_message(self) -> str:
        """ Returns the user's query. """
        greeting = "🤖 Hi, I'm Miney! I can search the web and extract lists of data for you. "
        question = "What information do you need?"
        user_response = input(greeting + question + "\n🧑 ")
        return user_response

    def rewrite(self, user_response: str) -> Tuple[str, Optional[str], str]:
        """ Parses the user's query into its components. """
        print("🤖 Analyzing your request...")
        FileManager.delete_files_by_extension(".json")
        return self._user_query_rewriter.rewrite(user_response)

    def search(self, search_query: str) -> List[str]:
        """ Performs a web search using Google's API. """
        print(f"🤖 Searching for '{search_query}'...")
        self._search.set_query(search_query)
        urls = []
        results = True
        while results:
            results = self._search.next_urls()
            urls.extend(results)
        return urls

    def open_browser(self) -> None:
        """ Starts Google Chrome. """
        if not self._browser:
            self._browser = Browser()
            self._page_inspector = PageInspector(self._browser)
            self._data_locator = DataLocator(self._browser)

    def browse(self, url: str, search_index: int) -> bool:
        """ Navigates to the URL and uses LLM vision to check for popups or captchas. """
        self._reset_scraper()
        print(f"🤖 Browsing {url}...")
        self._file_index = search_index + 1
        self._validator_failed = False
        self._browser.go_to_url(url)
        print("🤖 Checking if the page loaded correctly...")
        loading_failed, issue = self._page_inspector.identify_loading_issues()
        press_enter = "press Enter to continue..."
        if loading_failed:
            if issue == 'popup':
                input("🤖 Please close the popup and " + press_enter + "\n🧑 ")
            elif issue == 'captcha':
                skip = input("🤖 Please verify you are a human and " + press_enter +
                             "(or write 'skip' to browse another website)\n🧑 ")
                if skip:
                    return True
        return False

    def extract_data(self, user_intent: str) -> Tuple[Optional[ScrapedData], bool]:
        """ Uses LLMs to extract data from the web page based on the user's request. """
        file_name = f'data{self._file_index}'
        self._locate_data(user_intent, file_name)
        if self._scraping_attempts > 0:
            self._web_scraper.set_feedback(self._data, self._feedback)
        print("🤖 Extracting data from the page...")
        self._web_scraper.scrape(user_intent, file_name)
        print("🤖 Checking the data is correct...")
        self._validator = Validator()
        self._data = self._validator.load_data_file(self._browser.get_url(), file_name)
        if not self._data or not self._validator.validate(user_intent):
            no_data_message = 'No data extracted from the page.'
            print(f"🤖 No valid data found: {self._validator.error if self._data else no_data_message}")
            self._data = None
            if not self._validator_failed:
                self._validator_failed = True
                return None, False
            return None, True # Skip the current page if two failed attempts
        return self._data, False

    def _locate_data(self, user_intent: str, file_name: str) -> None:
        """ Identifies the HTML elements that contain the data the user requested. """
        print("🤖 Searching for page elements that contain data...")
        if self._feedback:
            self._data_locator.set_feedback(self._feedback)
        data_sample, data_type = self._data_locator.find(user_intent, file_name, self._scraping_attempts)
        self._web_scraper.set_source(data_sample, data_type)

    def open_json_file(self) -> None:
        """ Opens the JSON file containing the scraped data using the default text editor. """ 
        if self._data:
            self._file_manager.open_file(f'data{self._file_index}.json')

    def user_validates(self, data: Optional[ScrapedData], skip_url: bool) -> Tuple[bool, bool]:
        """ Prompts the user to validate the scraped data or skip to another URL. """
        if skip_url:
            return False, True
        max_attempts = self._scraping_attempts >= AppManager.MAX_USER_VALIDATIONS_PER_WEBSITE
        self._scraping_attempts += 1
        if not data or not self._data:
            self._feedback = None
            return False, max_attempts
        question = "🤖 Here's what I found, is this the data you need? \n"
        if not max_attempts:
            prompt = "   - Write 'yes' to keep this data.\n"
            prompt += "   - Write 'skip' to browse another website.\n"
            prompt += "   - Or give me some feedback and I'll try again."
        else:
            prompt = "🤖 Write 'yes' to keep this data or press Enter to browse another website."
        self._feedback = input(question + prompt + "\n🧑 ")
        data_valid = "yes" in self._feedback.lower()
        if self._feedback.lower() == "skip":
            max_attempts = True
        if not data_valid and self._file_index > Search.MAX_RESULTS:
            print("🤖 Let's keep looking...\n")
        return data_valid, max_attempts
    
    def _reset_scraper(self) -> None:
        """ Resets the scraper and associated components for a new browsing session. """
        self._page_inspector = PageInspector(self._browser)
        self._data_locator = DataLocator(self._browser)
        self._web_scraper = WebScraper()
        self._validator = Validator()
        self._scraping_attempts = 0
        self._feedback = None

    def display_source_info(self) -> None:
        """ Displays the file name, URL and cost of the session. """
        FileManager.delete_files_by_extension(".html")
        if not self._validator.data:
            print("🤖 No valid data found. Please try again.")
        else:
            print(f"🤖 Data saved as data{self._file_index}.json.")
            print(f"   Source: {self._browser.get_url()}")
            cost = round(Conversation.total_cost, 2)
            print(f"   Estimated cost: {'< $0.01' if cost < 0.01 else f'${cost}'}")        
        self._browser.close()
