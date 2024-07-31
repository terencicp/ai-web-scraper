import unittest
from helper import add_app_to_path

add_app_to_path(levels=3)
from app.search.Search import Search


class TestSearch(unittest.TestCase):

    def setUp(self):
        self.search = Search()
        self.search.set_query("Test query")

    def test_constructor(self):
        # Check if the constructor creates the correct API parameters
        self.assertIn('key', self.search._request_parameters)
        self.assertIn('cx', self.search._request_parameters)
        self.assertEqual(self.search._request_parameters['q'], "Test query")
        self.assertEqual(self.search._request_parameters['start'], 1)

    def test_max_results_reached(self):
        # Check if the maximum number of search results have been returned
        self.search._total_results = 5
        self.search.MAX_RESULTS = 10
        self.assertFalse(self.search._max_results_reached())

    def test_set_start_index(self):
        # Check if the pagination index is updated correctly from JSON
        mock_json_response = {'queries': {'nextPage': [{'startIndex': 11}]}}
        self.search._set_start_index(mock_json_response)
        self.assertEqual(self.search._request_parameters['start'], 11)

    def test_extract_urls(self):
        # Check if the URLs are extracted correctly from the JSON response
        json_response = {"items": [{"link": "https://example.com"}]}
        actual_urls = self.search._extract_urls(json_response)
        self.assertEqual(actual_urls, ["https://example.com"])

if __name__ == '__main__':
    unittest.main()