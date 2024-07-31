from enum import Enum

class DataType(Enum):
    """ Type of html sample extracted from the web page. """
    DATA_NOT_FOUND = 'data not found'
    TABLE = 'table'
    TEXT = 'text'
    FIRST_ITEM = 'first item'
    DISTINCT_ITEMS = 'distinct items'
    CONTAINER = 'container'