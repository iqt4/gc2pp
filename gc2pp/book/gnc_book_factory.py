import enum
from dataclasses import dataclass
from pathlib import Path

from .xml_book import XMLBook
from .gnc_book import GncBook


class GncType(enum.Enum):
    """Gnucash storage format. Only XML file implemented"""
    XML = "xml"


@dataclass
class GncObject:
    gnc_type: GncType = None
    filename: Path = None


class GncBookFactory:
    """Factory class to open Gnucash Book"""

    @staticmethod
    def open(gnc_object: GncObject) -> GncBook:
        if gnc_object.gnc_type == GncType.XML:
            return XMLBook(str(gnc_object.filename))
        else:
            raise Exception("Unknown Gnucash filetype")
