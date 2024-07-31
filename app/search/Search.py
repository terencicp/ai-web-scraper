import os
import sys
import time
from typing import Any, Dict, List, Optional

import requests
from requests.exceptions import RequestException


class Search:
    """
    Searches using Google's Custom Search JSON API. Returns an empty list if MAX_RESULTS is reached.

    Usage example:
        search = Search()
        search.set_query('Search query')
        url_list_page_1 = search.next_urls()

    Requirements:
        Environment variables 'GOOGLE_SEARCH_API_KEY' and 'GOOGLE_SEARCH_ID'.
    """

    API_URL = 'https://www.googleapis.com/customsearch/v1'
    API_KEY = os.getenv('GOOGLE_SEARCH_API_KEY')
    API_ID = os.getenv('GOOGLE_SEARCH_ID')

    MAX_RESULTS = 9
    TIMEOUT = 10
    REQUEST_TRIES = 3
    SECONDS_BETWEEN_RETRIES = 5

    def __init__(self) -> None:
        self._request_parameters = {
            'key': self.API_KEY,
            'cx': self.API_ID,
            'q': None,
            'start': 1 # Index for pagination
        }
        self._total_results = 0

    def set_query(self, query: str) -> None:
        """ Sets the search query. """
        self._request_parameters['q'] = query

    def _max_results_reached(self) -> bool:
        """ Checks if the maximum number of results has been reached. """
        return self._total_results >= self.MAX_RESULTS

    def _request_json(self) -> Dict[str, Any]:
        """ Sends a request to the API and returns the JSON response. """
        response = requests.get(self.API_URL, self._request_parameters, timeout=self.TIMEOUT)
        response.raise_for_status()
        return response.json()

    def _attempt_request(self) -> Optional[Dict]:
        """ Send a request to the API, retry if it fails. """
        if not self.API_KEY or not self.API_ID:
            sys.exit("Missing search API key or ID.")
        for _ in range(self.REQUEST_TRIES):
            try:
                return self._request_json()
            except RequestException as error:
                print("Search request error:", error)
                time.sleep(self.SECONDS_BETWEEN_RETRIES)
        return None

    def _set_start_index(self, json_response: Dict) -> None:
        """ Updates the 'start' parameter for pagination. """
        next_page_start_index = json_response['queries']['nextPage'][0]['startIndex']
        self._request_parameters['start'] = next_page_start_index

    def _extract_urls(self, json_response: Dict) -> List[str]:
        """ Converts the JSON response into a list of URLs. """
        urls = []
        for item in json_response.get('items', []):
            if 'link' in item:
                urls.append(item['link'])
        return urls

    def _fetch_urls(self) -> List[str]:
        """ Fetches URLs from the API and sets the pagination index. """
        json_response = self._attempt_request()
        if json_response:
            self._set_start_index(json_response)
            urls = self._extract_urls(json_response)
            remaining = self.MAX_RESULTS - self._total_results
            urls = urls[:remaining]
            self._total_results += len(urls)
            return urls
        else:
            return []

    def next_urls(self) -> List[str]:
        """ Fetches the next page of URLs from the API. """
        if self._max_results_reached():
            return []
        else:
            return self._fetch_urls()
