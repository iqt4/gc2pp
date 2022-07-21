from __future__ import annotations
import argparse
import enum
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, timedelta, MINYEAR
from pathlib import Path
from urllib.parse import urlparse
from book import GncType, GncObject, GncBookFactory


class PPType(enum.Enum):
    ACCOUNT = "account"
    PORTFOLIO = "portfolio"
    INTEREST = "interest"
    FEES = "fees"
    TAXES = "taxes"
    DIVIDENDS = "dividends"


@dataclass
class MappingItem:
    pp_type: PPType
    gnc_account_names: list[str]
    pp_name: str = None


class Configuration(object):
    """Container for all configuration objects"""

    def __init__(self) -> None:
        """We need configuration parameters"""
        self.filename = None
        self.date: date = date(MINYEAR, 1, 1)
        self.items: dict[MappingItem] = {}
        self.gnc_object: GncObject = GncObject()


class IConfigHandler(ABC):
    """Abstract Handler"""

    def __init__(self, successor) -> None:
        self._successor = successor

    def handle(self, request: Configuration):
        handled = self._handle(request)

        if not handled and self._successor.handle is not None:
            self._successor.handle(request)

    @abstractmethod
    def _handle(self, request):
        pass


class ConfigDefault(IConfigHandler):
    """Set the default parameters"""

    def _handle(self, conf: Configuration):

        conf.date = date.today() - timedelta(days=30)

        filename = Path('./gc2pp.json').resolve()
        if filename.is_file():
            conf.filename = filename


class ConfigCommandLine(IConfigHandler):
    """Configuration from arguments"""

    def _handle(self, conf: Configuration):
        parser = argparse.ArgumentParser(description='Convert Gnucash file to Portfolio Performance CSV')
        parser.add_argument('-c', '--conf', help='Configuration file')
        parser.add_argument('-u', '--url', help='Gnucash format [file://filename]')
        parser.add_argument('-d', '--date', help='first conversion date')
        args = parser.parse_args()

        if args.conf is not None:
            filename = Path(args.conf).resolve()
            if filename.is_file():
                conf.filename = filename
            else:
                raise FileNotFoundError

        if args.url is not None:
            url = urlparse(args.uri, scheme='file')
            if url.scheme == 'file':
                filename = Path(url.netloc).resolve()
                if filename.is_file():
                    conf.gnc_object = GncObject(filetype=GncType.XML, filename=filename)
                else:
                    raise FileNotFoundError
            else:
                raise ValueError(url)

        if args.date is not None:
            # ToDo: Implement date parameter
            pass


class ConfigFile(IConfigHandler):
    """Read from configuration file"""

    def _handle(self, conf: Configuration):
        def item_decoder(dct: dict):
            if "pp_type" in dct:
                try:
                    pp_type = PPType(dct["pp_type"])
                    if pp_type in (pp_type.ACCOUNT, pp_type.PORTFOLIO) and "pp_name" in dct:
                        dct = MappingItem(pp_type, dct["gnc_account_names"], dct["pp_name"])
                    else:
                        dct = MappingItem(pp_type, dct["gnc_account_names"])
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

        if conf.filename is not None:
            with open(conf.filename, 'r') as f:
                json_conf = json.load(f, object_hook=item_decoder)
                conf.items = json_conf["items"]
                if conf.gnc_object is not None and json_conf["gnc_object"] is not None:
                    conf.gnc_object = json_conf["gnc_object"]

        # ToDo: Sanity check of the items

        return True


class ConfigurationFactory(object):

    @staticmethod
    def load() -> Configuration:
        c = Configuration()
        handler = ConfigDefault(ConfigCommandLine(ConfigFile(None)))
        handler.handle(c)
        return c


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
