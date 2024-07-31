class StringUtils:
    """ Utility class for string operations. """

    @staticmethod
    def trim_with_ellipsis(text: str, max_length: int) -> str:
        """ Trims the text to the maximum length and adds an ellipsis if it's longer. """
        if len(text) < max_length:
            return text
        return text[:max_length] + ' ...'

    @staticmethod
    def split_with_ellipsis(text: str, max_length: int) -> str:
        """ Splits the text in half and adds an ellipsis if it is longer. """
        if len(text) < max_length:
            return text
        half_limit = max_length // 2
        return text[:half_limit] + "..." + text[-half_limit:]
