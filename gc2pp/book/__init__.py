from .book import GncBook, GncCommodity, GncSplit, GncTransaction, GncAccount
from .xml_book import XMLBook

GncBook.register(XMLBook)
