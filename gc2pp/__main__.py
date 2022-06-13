from pathlib import Path
from config import get_config
from book import GncBook

print(Path('./data').resolve())
config = get_config()
filename = "/Users/dirk/Development/PycharmProjects/Haushalt.gnucash.gz"
print(Path(filename).resolve(strict=True))
gnc_book = GncBook.open(filename)
gnc_securities = [c for c in gnc_book.commodities if c.space not in ['CURRENCY', 'template']]
pass
