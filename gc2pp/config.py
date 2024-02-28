from __future__ import annotations
import argparse
import enum
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, timedelta
from dateutil.parser import parse as dateparse
from pathlib import Path
from urllib.parse import urlparse
from book import GncType, GncObject


class MappingType(enum.Enum):
    # PP transaction owners mapped to GncAccounts
    ACCOUNT = "account"
    PORTFOLIO = "portfolio"
    
    # PP AccountTransaction types mapped to GncAccounts
    INTEREST = "interest" # INTEREST(false), INTEREST_CHARGE(true)
    FEES = "fees" # FEES(true), FEES_REFUND(false)
    TAXES = "taxes" # TAXES(true), TAX_REFUND(false)
    DIVIDENDS = "dividends" # DIVIDENDS(false)

    # Other PP AccountTransaction types are derived from transfer between GncAccounts
    """
    DEPOSIT(false), REMOVAL(true), --> Transfer into/out of the account
    BUY(true), SELL(false), --> Transfer between account and portfolio (incl. tax and fees)
    TRANSFER_IN(false), TRANSFER_OUT(true) --> Transfer between accounts
    """        

@dataclass
class MappingItem:
    type: MappingType
    gnc_account_names: list[str]
    pp_name: str = None
    

class Configuration(object):
    """Container for all configuration items"""

    def __init__(self) -> None:
        """We need configuration parameters"""
        # configuration filename
        self.filename = None
        self.date: date = None
        self.items: dict[MappingItem] = {}
        self.gnc_object: GncObject = None
    
    def is_valid(self) -> bool:
        """Validate completeness"""
        if self.filename is None or self.date is None or self.items is None or self.gnc_object is None:
            return False
        
        return True


class IConfigHandler(ABC):
    """Abstract Handler"""

    def __init__(self, successor) -> None:
        self._successor = successor

    def handle(self, request: Configuration):
        handled = self._handle(request)

        if not handled and self._successor is not None:
            self._successor.handle(request)

    @abstractmethod
    def _handle(self, request):
        pass


class ConfigDefault(IConfigHandler):
    """Validate parameters"""

    def _handle(self, conf: Configuration):
        if conf.date is None:
            conf.date = date.today() - timedelta(days=30)


class ConfigCommandLine(IConfigHandler):
    """Configuration from arguments"""

    def _handle(self, conf: Configuration):
        parser = argparse.ArgumentParser(description='Convert Gnucash file to Portfolio Performance CSV')
        parser.add_argument('-c', '--conf', help='Configuration file', default='./data/gc2pp.json')
        parser.add_argument('-u', '--url', help='Gnucash source format [file://filename]')
        parser.add_argument('-d', '--date', help='First conversion date')
        args = parser.parse_args()

        # We need a configuration file
        filename = Path(args.conf).resolve()
        if filename.is_file():
            conf.filename = filename
        else:
            raise FileNotFoundError

        if args.url is not None:
            # ToDo only xml is valid for now. See https://www.gnucash.org/docs/v5/C/gnucash-guide/basics-files1.html
            url = urlparse(args.url, scheme='file')
            if url.scheme == 'file':
                filename = Path(url.path).resolve()
                if filename.is_file():
                    conf.gnc_object = GncObject(gnc_type=GncType.XML, filename=filename)
                else:
                    raise FileNotFoundError
            else:
                raise ValueError(url)

        if args.date is not None:
            conf.date = dateparse(args.date).date


class ConfigFile(IConfigHandler):
    """Read from configuration file"""

    def _handle(self, conf: Configuration):
        def item_decoder(dct: dict):
            if "pp_type" in dct:
                try:
                    type = MappingType(dct["pp_type"])
                    if type in (type.ACCOUNT, type.PORTFOLIO) and "pp_name" in dct:
                        dct = MappingItem(type, dct["gnc_account_names"], dct["pp_name"])
                    else:
                        dct = MappingItem(type, dct["gnc_account_names"])
                except ValueError:
                    print(f"Invalid item: {dct}")
                    dct = None

            elif "gnc_type" in dct:
                try:
                    gnc_type = GncType(dct["gnc_type"])
                    gnc_filename = Path(dct["gnc_filename"]).resolve()
                    if gnc_filename.is_file():
                        dct = GncObject(gnc_type, gnc_filename)
                    else:
                        dct = None
                except ValueError:
                    print(f"Invalid item: {dct}")
                    dct = None

            return dct

        with open(conf.filename, 'r') as f:
            json_conf = json.load(f, object_hook=item_decoder)
            conf.items = json_conf["items"]
            # ToDo: Sanity check of the items

            if conf.gnc_object is None and "gnc_object" in json_conf:
                conf.gnc_object = json_conf["gnc_object"]

            if conf.date is None and "due_date" in json_conf:
                conf.date = dateparse(json_conf["due_date"]).date


class ConfigurationFactory(object):

    @staticmethod
    def load() -> Configuration:
        c = Configuration()
        # First read the command line, then the configuration file
        # Finally set default values
        handler = ConfigCommandLine(ConfigFile(ConfigDefault(None)))
        handler.handle(c)
        if c.is_valid():
            return c
        else:
            return None


if __name__ == '__main__':
    c = ConfigurationFactory.load()

    pass


# def get_accounts(book):
#     accounts = dict()
#
#     # find all stock accounts, except currencies and template
#     accounts['stocks'] = piecash._common.CallableList([c for c in book.commodities
#                         if c.namespace not in ['CURRENCY', 'template']])
#
#     for k, v in _gnc_accounts.items():
#         if isinstance(v, list):
#             accounts[k] = [book.accounts(fullname=i) for i in v]
#         else:
#             accounts[k] = book.accounts(fullname=v)
#
#     return (accounts)
#


# def save_ini(para):
#     def to_json(python_object):
#         if isinstance(python_object, dt.datetime):
#             #            return {'__class__': 'datetime',
#             #                '__value__': python_object.date().isoformat()}
#             return python_object.date().isoformat()
#         elif isinstance(python_object, piecash.core.account.Account):
#             return python_object.fullname.encode('utf-8')
#         raise TypeError(repr(python_object) + ' is not JSON serializable')
#
#     para_exp = {k: v for k, v in para.items()
#                 if k in ['gnc_file', 'due_date']}
#
#     accounts = {p: para[p] for p in para
#                 if p in ['gnc_portfolio', 'gnc_dividend', 'gnc_account',
#                          'gnc_charge', 'gnc_tax', 'gnc_dividend', 'gnc_day2day']}
#
#     para_exp['accounts'] = accounts
#
#     with open('../data/pc.json', 'w') as f:
#         json.dump(para_exp, f, ensure_ascii=False, indent=4, default=to_json)
