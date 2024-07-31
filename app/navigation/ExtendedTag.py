from __future__ import annotations
from copy import deepcopy
from typing import List, Optional

from bs4 import Tag
from htmlmin import minify
from bs4 import Comment

from app.ai.utils.StringUtils import StringUtils


class ExtendedTag(Tag):
    """ Adds helper methods to the Tag class from BeautifulSoup. """

    name: str

    def __init__(
        self, parser=None, builder=None, name=None, namespace=None,
        prefix=None, attrs=None, parent=None, previous=None,
        is_xml=None, sourceline=None, sourcepos=None,
        can_be_empty_element=None, cdata_list_attributes=None,
        preserve_whitespace_tags=None,
        interesting_string_types=None,
        namespaces=None
    ):
        super().__init__(
            parser, builder, name, namespace,
            prefix, attrs, parent, previous,
            is_xml, sourceline, sourcepos,
            can_be_empty_element, cdata_list_attributes,
            preserve_whitespace_tags,
            interesting_string_types,
            namespaces
        )

    def is_identical_to(self, other: ExtendedTag) -> bool:
        """ True if two tags have the same name and attributes, ignoring the id. """
        if self.name != other.name:
            return False
        self_attrs = {k: v for k, v in self.attrs.items() if k != 'id'}
        other_attrs = {k: v for k, v in other.attrs.items() if k != 'id'}
        return self_attrs == other_attrs

    def is_text_tag(self) -> bool:
        """ True if the tag is a paragraph, header or list. """
        return self.name in ['p', 'ul', 'ol', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
    
    def remove_children_style(self) -> ExtendedTag:
        """ Removes the style attribute from all direct children of the tag. """
        for child in self.find_all(recursive=False):
            if 'style' in child.attrs:
                del child.attrs['style']
        return self
    
    def is_descendant_of(self, other: ExtendedTag) -> bool:
        """ Returns True if self is a descendant of other. """
        return bool(self != other and self in other.descendants)
    
    def find_parent_table(self) -> Optional[ExtendedTag]:
        """ Returns the parent table tag if the element is part of a table. """
        if self.name == 'table':
            return self
        return self.find_parent('table')
    
    def get_first_rows(self, n: int) -> Optional[ExtendedTag]:
        """ Returns a copy of the table with only the first n rows. """
        if self.name != 'table':
            return None
        table_copy = self.copy()
        rows = table_copy.find_all('tr')
        for row in rows[n:]:
            row.decompose()
        return table_copy

    def copy(self) -> ExtendedTag:
        """ Returns a deep copy of the tag. """
        return deepcopy(self)

    def shorten_text(self, nchars: int) -> ExtendedTag:
        """ Shortens all strings in the HTML. """
        for element in self.find_all():
            if element.string and len(element.string) > nchars:
                element.string = element.string[:nchars] + '...'
        return self
    
    def remove_tags(self, tags: List[str]) -> ExtendedTag:
        """ Removes all the given tags from the element. """
        for tag in tags:
            for element in self.find_all(tag):
                element.decompose()
        return self

    def strip_attributes(self, strip: List[str]) -> ExtendedTag:
        """ Strips the specified attributes from all elements. """
        for element in self.find_all():
            for attr in strip:
                if attr in element.attrs:
                    del element.attrs[attr]
        return self
    
    def remove_comments(self) -> ExtendedTag:
        """ Removes all HTML comments from the element. """
        for comment in self.find_all(text=lambda text: isinstance(text, Comment)):
            comment.extract()
        return self
    
    def shorten_src(self, max_length: int) -> ExtendedTag:
        """ Shortens all src attribute values to a maximum length. """
        for element in self.find_all(attrs={'src': True}):
            element['src'] = StringUtils.trim_with_ellipsis(element['src'], max_length)
        return self
    
    def clear_svg_contents(self) -> ExtendedTag:
        """ Delete all children from svg tags inside the current tag. """
        for svg in self.find_all('svg'):
            for child in list(svg.children):
                if isinstance(child, Tag):
                    child.decompose()
        return self

    def minify(self) -> str:
        """ Removes unnecessary whitespace from the HTML. """
        return minify(str(self))
