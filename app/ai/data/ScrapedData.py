from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class ScrapedData:
    """ Contains data scraped from a web page, source url and the name of the file where it's stored. """

    file_name: str
    url: str
    content: Optional[List[Dict]] = None

    @property
    def length(self):
        return len(self.content) if self.content else 0

    def __str__(self):
        if self.content is None:
            return ""
        return str(self.content)