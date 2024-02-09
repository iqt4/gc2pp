from pathlib import Path
from config import ConfigurationFactory
from book import GncBookFactory

print(Path('../data').resolve())
config = ConfigurationFactory.load()
print(Path(config.filename).resolve(strict=True))
gnc_book = GncBookFactory().open(config.gnc_object)
gnc_securities = [c for c in gnc_book.commodities if c.space not in ['CURRENCY', 'template']]
pass
