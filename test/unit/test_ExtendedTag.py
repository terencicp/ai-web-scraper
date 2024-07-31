import unittest
from helper import add_app_to_path

add_app_to_path(levels=3)
from app.navigation.ExtendedBeautifulSoup import ExtendedBeautifulSoup as BS
from app.navigation.ExtendedTag import ExtendedTag as Tag


class TestExtendedTag(unittest.TestCase):

    def setUp(self):

        # Set up an HTML document to use in tests
        self.html = '''<html>
            <body>
                <p>This is a long paragraph that should be shortened.</p>
                <p id="p1" style="color:red;">This is a short one.</p>
                <script>Remove this script</script>
                <style>Remove this style</style>
                <div>Keep this div</div>
                <div>
                    <p>Nested paragraph that is long and should be shortened.</p>
                    <script>Nested script</script>
                    <style>Nested style</style>
                    <div>Nested div</div>
                    <p id="p2" style="color:red;">Nested paragraph.</p>
                </div>
                <img src="https://example.com/very/long/path/to/image1.jpg" alt="Image 1">
                <iframe src="https://example.com/embed/very/long/path/to/video1" width="560" height="315"></iframe>
            </body>
        </html>'''
        self.soup = BS(self.html, 'html.parser')
        self.extended_tag = self.soup.body

    def test_is_identical_to(self):
        # Test if two tags with the same name and attributes (excluding id) are identical
        tag1 = Tag(name='div', attrs={'class': 'test', 'id': '1'})
        tag2 = Tag(name='div', attrs={'class': 'test', 'id': '2'})
        self.assertTrue(tag1.is_identical_to(tag2))

    def test_is_text_tag(self):
        # Test if a paragraph tag is recognized as a text tag
        tag = Tag(name='p')
        self.assertTrue(tag.is_text_tag())

    def test_remove_children_style(self):
        # Test if style attribute is removed from direct children
        parent = Tag(name='div')
        child = Tag(name='p', attrs={'style': 'color: red;'})
        parent.append(child)
        parent.remove_children_style()
        self.assertNotIn('style', child.attrs)

    def test_is_descendant_of(self):
        # Test if a tag is recognized as a descendant of another tag
        parent = Tag(name='div')
        child = Tag(name='p')
        parent.append(child)
        self.assertTrue(child.is_descendant_of(parent))

    def test_find_parent_table(self):
        # Test if the parent table is found correctly
        table = Tag(name='table')
        row = Tag(name='tr')
        cell = Tag(name='td')
        table.append(row)
        row.append(cell)
        self.assertEqual(cell.find_parent_table(), table)

    def test_get_first_rows(self):
        # Test if only the first n rows of a table are returned
        table = Tag(name='table')
        for _ in range(5):
            table.append(Tag(name='tr'))
        result = table.get_first_rows(3)
        self.assertEqual(len(result.find_all('tr')), 3)

    def test_copy(self):
        # Test if a deep copy of the tag is created
        original = Tag(name='div', attrs={'class': 'test'})
        copy = original.copy()
        self.assertIsNot(original, copy)
        self.assertEqual(original.name, copy.name)
        self.assertEqual(original.attrs, copy.attrs)

    def test_shorten_text(self):
        # Test if text content is shortened correctly
        div = Tag(name='div')
        p = Tag(name='p')
        p.string = 'This is a long text'
        div.append(p)
        div.shorten_text(1)
        self.assertEqual(p.string, 'T...')

    def test_remove_tags(self):
        # Test if specified tags are removed from the element
        parent = Tag(name='div')
        parent.append(Tag(name='p'))
        parent.append(Tag(name='span'))
        parent.remove_tags(['span'])
        self.assertIsNone(parent.find('span'))

    def test_strip_attributes(self):
        # Test if specified attributes are stripped from all elements
        attributes_to_strip = ['id', 'style']
        self.extended_tag.strip_attributes(attributes_to_strip)
        for element in self.extended_tag.find_all():
            for attr in attributes_to_strip:
                self.assertNotIn(attr, element.attrs)

    def test_shorten_src_attributes(self):
        # Test if src attributes are shortened correctly
        self.extended_tag.shorten_src(max_length=30)
        img = self.extended_tag.find('img')
        iframe = self.extended_tag.find('iframe')
        self.assertEqual(img['src'], 'https://example.com/very/long/ ...')
        self.assertEqual(iframe['src'], 'https://example.com/embed/very ...')

if __name__ == '__main__':
    unittest.main()