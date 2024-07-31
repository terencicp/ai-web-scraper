from typing import Optional

from app.ai.data.ScrapedData import ScrapedData
from app.ai.agents.Validator import Validator


class FeedbackData:
    """ A sample of the scraped data and feedback about how to improve the scraping process. """

    def __init__(self,
            data: Optional[ScrapedData],
            description: Optional[str]
        ):
        self.sample = Validator.get_data_item_sample(data) if data else ""
        self.data_length = data.length if data else 0
        self.description = description if description else ""