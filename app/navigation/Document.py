from bs4 import Comment, NavigableString
from typing import List, Optional

from app.navigation.ExtendedBeautifulSoup import ExtendedBeautifulSoup as BS
from app.navigation.ExtendedTag import ExtendedTag as Tag

class Document:
    """
    Represents the body of an HTML document, with methods to manipulate it.

    Usage example:
        document = Document(html_list)
        document_text = document.get_text(100)
        elements = document.find_elements_by_text('example')
        common_ancestor = document.find_common_ancestor(elements[0], elements[1])
        ancestors = document.find_ancestors(elements[0], elements[0].parent.parent)
        family = document.get_family(elements[0])
        distinct_children = document.find_distinct_children(elements[0])
        document.update(new_html_list)
    """

    def __init__(self, html_list: List[str]) -> None:
        """ Initializes the Document with an empty body and immediately updates it. """
        self.html: Optional[BS] = None
        self.body: Optional[Tag] = None
        self.update(html_list)

    def update(self, html_list: List[str]) -> None:
        """ Refresh the HTML body contents. """
        self.html = self._combine_documents(html_list)
        self.body = self.html.body

    def _combine_documents(self, html_list: List[str]) -> BS:
        """ Adds the body contents of multiple html documents to a main document. """
        main_soup = BS(html_list[0], 'html.parser')
        for html in html_list[1:]:
            secondary_soup = BS(html, 'html.parser')
            body = secondary_soup.body
            if not body:
                continue
            for child in body.children:
                if isinstance(child, Tag):
                    main_soup.body.append(self._copy_tag(child, main_soup))
                else:
                    main_soup.body.append(main_soup.new_string(str(child)))
        return main_soup

    def _copy_tag(self, src_tag: Tag, dest_soup: BS) -> Tag:
        """ Recursively copy a tag and its content. """
        attributes_except_name = {k: v for k, v in src_tag.attrs.items() if k != 'name'}
        new_tag = dest_soup.new_tag(src_tag.name, **attributes_except_name)
        for child in src_tag.children:
            if isinstance(child, Tag):
                new_tag.append(self._copy_tag(child, dest_soup))
            else:
                new_tag.append(dest_soup.new_string(str(child)))
        return new_tag

    def get_text(self, max_length: int) -> str:
        """ Returns strings in HTML elements, shortening long ones. """
        if not self.body:
            return ''
        body_copy = self.body.copy()
        clean_body = body_copy.remove_tags(['script', 'style'])
        texts = self._extract_element_texts(clean_body)
        short_texts = []
        for text in texts:
            if len(text) > max_length:
                short_texts.append(text[:max_length] + '...')
            else:
                short_texts.append(text)
        return self._join_strings(short_texts)

    def _extract_element_texts(self, element: Tag) -> List[str]:
        """ Extracts strings from HTML elements. """
        texts = []
        for child in element.children:
            if isinstance(child, Comment):
                continue
            elif isinstance(child, NavigableString):
                texts.append(child.string.strip())
            else:
                texts.extend(self._extract_element_texts(child))
        return texts

    def _join_strings(self, strings: List) -> str:
        """ Joins a list of strings without unnecessary whitespace. """
        return ' '.join(' '.join(strings).split())

    def find_elements_by_text(self, text: str) -> List[Tag]:
        """ Finds all HTML elements that contain a given string. """
        elements = self.body.find_all(lambda tag: self._tag_contains_text(tag, text))
        return elements
    
    def _tag_contains_text(self, tag: Tag, text: str) -> bool:
        return tag.string and tag.string.strip() == text

    def find_common_ancestor(self, element1: Tag, element2: Tag) -> Optional[Tag]:
        """ Finds the closest common ancestor of two HTML elements. """
        ancestors1 = list(element1.parents)
        ancestors2 = list(element2.parents)
        for ancestor1 in ancestors1:
            if ancestor1 in ancestors2:
                return ancestor1
        return None

    def find_ancestors(self, element: Tag, ancestor_limit: Tag) -> List[Tag]:
        """ Returns the ancestors of an HTML element up to the given ancestor. """
        ancestors = [element]
        current_element = element.parent
        while current_element != ancestor_limit:
            ancestors.append(current_element)
            current_element = current_element.parent
        ancestors.reverse()
        return ancestors

    def get_family(self, element: Tag) -> Optional[Tag]:
        """ Returns the parent and siblings of the HTML element (without the element). """
        if element.name == 'body':
            return None
        parent = element.parent.copy()
        parent.find(element.name, attrs=element.attrs).decompose()
        return parent
    
    def find_distinct_children(self, element: Tag) -> List[Tag]:
        """ Returns the children of the HTML element that are not similar. """
        distinct_children = []
        for child in element.children:
            if not isinstance(child, Tag):
                continue
            if not any(child.is_identical_to(distinct) for distinct in distinct_children):
                distinct_children.append(child)
        return distinct_children
