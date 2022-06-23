from .xml_book import XMLBook
from .gnc_book import GncBook


class GncBookFactory:
    """Factory class to open Gnucash Book"""

    @staticmethod
    def open(filetype, **kwargs) -> GncBook:
        if filetype == "xml":
            return XMLBook(kwargs['filename'])
        else:
            raise Exception("Unknown Gnucash filetype")
