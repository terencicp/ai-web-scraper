import unittest
from helper import add_app_to_path

add_app_to_path(levels=3)
from app.navigation.Document import Document
from app.navigation.ExtendedBeautifulSoup import ExtendedBeautifulSoup as BS


class TestDocument(unittest.TestCase):

    def setUp(self):
        # Create a Document from two HTML documents with whitespace
        two_html_docs = ['<html><body><p>  Hello World  </p></body></html>', '<html><body><p>Another Document</p></body></html>']
        self.doc = Document(two_html_docs)

    def test_update(self):
        # Calling update with a list with a single HTML document should extract the body
        self.doc.update(['<html><body><p>New Document</p></body></html>'])
        self.assertEqual(str(self.doc.body), '<body><p>New Document</p></body>')

    def test_combine_documents(self):
        # Combining two HTML documents should merge the body contents
        combined = self.doc._combine_documents(['<html><body><p>Doc 1</p></body></html>', '<html><body><p>Doc 2</p></body></html>'])
        self.assertEqual(str(combined), '<html><body><p>Doc 1</p><p>Doc 2</p></body></html>')

    def test_find_common_ancestor(self):
        # Finding a tag from a CSS selector
        element1 = self.doc.body.select_one('p:contains("Hello World")')
        element2 = self.doc.body.select_one('p:contains("Another Document")')
        common_ancestor = self.doc.find_common_ancestor(element1, element2)
        self.assertEqual(str(common_ancestor), '<body><p>  Hello World  </p><p>Another Document</p></body>')

    def test_copy_tag(self):
        # Test copying a tag with nested elements and attributes
        source_tag = BS('<div class="test"><p>Hello <span style="color: red;">World</span></p></div>', 'html.parser').div
        dest_soup = BS('<html><body></body></html>', 'html.parser')
        copied_tag = self.doc._copy_tag(source_tag, dest_soup)
        self.assertEqual(str(copied_tag), str(source_tag))

    def test_get_text(self):
        # Test if get_text extracts tag strings in different lines, handles comments and shortens long strings
        html = '<html><body><!-- This is a comment --><p> Short text </p><p>This is longer text that should be truncated because it exceeds the maximum length of 120 characters set in the get_text method</p></body></html>'
        self.doc.update([html])
        result = self.doc.get_text(120)
        expected = 'Short text This is longer text that should be truncated because it exceeds the maximum length of 120 characters set in the get_text...'
        self.assertEqual(result, expected)

    def test_find_ancestors(self):
        # Test if the tags from tag A to tag D are found, in descending order
        html = '<html><body id="D"><div id="C"><div id="B"><p id="A">Test</p></div></div></body></html>'
        self.doc.update([html])
        D = self.doc.body
        A = D.find('p', id='A')
        ancestors = self.doc.find_ancestors(A, D)
        self.assertEqual(len(ancestors), 3)
        self.assertEqual(ancestors[0].get('id'), 'C')

    def test_get_family(self):
        # Test if the method extracts the parent and siblings but not the target tag
        html = '<html><body><div id="parent"><p id="sibling1">Sibling 1</p><p id="target">Target</p><p id="sibling2">Sibling 2</p></div></body></html>'
        self.doc.update([html])
        target = self.doc.body.find(id='target')
        parent = self.doc.get_family(target)
        self.assertEqual(parent.get('id'), 'parent')
        self.assertEqual(len(parent.contents), 2)
        self.assertIsNone(parent.find(id='target'))

    def test_find_distinct_children(self):
        # Create a sample HTML structure
        html = '''<div><p class="test">Paragraph 1</p><p class="test">Paragraph 2</p><span>Span 1</span><p class="different">Paragraph 3</p><span>Span 2</span></div>'''
        soup = BS(html, 'html.parser')
        root = soup.div
        distinct_children = self.doc.find_distinct_children(root)
        self.assertEqual(len(distinct_children), 3)
        self.assertEqual(distinct_children[0].name, 'p')
        self.assertEqual(distinct_children[1].name, 'span')
        self.assertEqual(distinct_children[2].name, 'p')

if __name__ == '__main__':
    unittest.main()