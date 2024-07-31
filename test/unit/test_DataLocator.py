import unittest
from unittest.mock import Mock
from helper import add_app_to_path

add_app_to_path(levels=3)
from app.ai.agents.DataLocator import DataLocator
from app.navigation.ExtendedBeautifulSoup import ExtendedBeautifulSoup as BS
from app.navigation.ExtendedTag import ExtendedTag as Tag
from app.ai.data.DocumentData import DocumentData as DocumentData


class TestDataLocator(unittest.TestCase):

    def setUp(self):
        self.browser_mock = Mock()
        self.locator = DataLocator(self.browser_mock)

    def test_extract_values(self):
        # Test with a string
        self.assertEqual(self.locator._extract_values("test"), ["test"])
        # Test with a number
        self.assertEqual(self.locator._extract_values(123), ["123"])
        # Test with a dictionary
        test_dict = {"a": 1, "b": "two", "c": [3, "four"]}
        expected = ["1", "two", "3", "four"]
        self.assertEqual(sorted(self.locator._extract_values(test_dict)), sorted(expected))
        # Test with a list
        test_list = [1, "two", {"three": 3}, [4, "five"]]
        expected = ["1", "two", "3", "4", "five"]
        self.assertEqual(sorted(self.locator._extract_values(test_list)), sorted(expected))

    def test_pairs(self):
        # Checks that all combinations of elements of two lists are returned
        list_a = [1, 2]
        list_b = ['a', 'b']
        expected_pairs = [(1, 'a'), (1, 'b'), (2, 'a'), (2, 'b')]
        self.assertEqual(self.locator._pairs(list_a, list_b), expected_pairs)

    def test_filter_unique_containers(self):
        # Checks duplicated data containers are removed
        container1 = Mock(spec=Tag)
        container2 = Mock(spec=Tag)
        data1 = DocumentData(container1, Mock(), Mock())
        data2 = DocumentData(container2, Mock(), Mock())
        data3 = DocumentData(container1, Mock(), Mock())  # Duplicate container
        input_data = [data1, data2, data3]
        filtered_data = self.locator._filter_unique_containers(input_data)
        containers = [data.container for data in filtered_data]
        expected_containers = {container1, container2}
        self.assertEqual(set(containers), expected_containers)

if __name__ == '__main__':
    unittest.main()