from bs4 import BeautifulSoup
from typing import Any

from app.navigation.ExtendedTag import ExtendedTag

class ExtendedBeautifulSoup(BeautifulSoup):

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """ Turn tags into ExtendedTags when creating a BeautifulSoup object. """
        super().__init__(*args, **kwargs)
        for tag in self.find_all():
            tag.__class__ = ExtendedTag

    def new_tag(self, name, *args, **kwargs):
        """ Turn newly created tags into ExtendedTags. """
        tag = super().new_tag(name, *args, **kwargs)
        tag.__class__ = ExtendedTag
        return tag