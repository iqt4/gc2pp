from pathlib import Path
from config import ConfigurationLoader
from book import GncBookFactory

print(Path('../data').resolve())
config = ConfigurationLoader.read()
filename = "/Users/dirk/Development/PycharmProjects/Haushalt.gnucash.gz"
print(Path(filename).resolve(strict=True))
gnc_book = GncBookFactory().open("xml", filename=filename)
gnc_securities = [c for c in gnc_book.commodities if c.space not in ['CURRENCY', 'template']]
pass
