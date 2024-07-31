from dataclasses import dataclass
from typing import Optional
from app.navigation.ExtendedTag import ExtendedTag as Tag

@dataclass
class DocumentData:
    """ Html element that contains data, elements used to find it and proportion of data it contains. """
    container: Optional[Tag] = None
    element1: Optional[Tag] = None
    element2: Optional[Tag] = None
    proportion: float = 0.0