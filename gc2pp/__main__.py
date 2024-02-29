from pathlib import Path
from config import ConfigurationFactory
from book import GncBookFactory

print(Path('../data').resolve())
config = ConfigurationFactory.load()
print(Path(config.filename).resolve(strict=True))
gnc_book = GncBookFactory().open(config.gnc_object)
print(gnc_book.find_account_by_name(""))
gnc_securities = [c for c in gnc_book.commodities if c.space not in ['CURRENCY', 'template']]
pass
