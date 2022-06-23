from __future__ import annotations
from sys import argv
import json
from abc import ABC, abstractmethod
from pathlib import Path
from book import GncBook, GncAccount


class PPAccount(object):
    _name: str
    _accounts: list[GncAccount]

    def __init__(self, name, accounts) -> None:
        self._name = name
        self._accounts = accounts

    @property
    def name(self) -> str:
        return self._name

    @property
    def accounts(self) -> list[GncAccount]:
        return self._accounts


class Configuration(object):

    def __init__(self):
        self._type: str
        filename: str


class IConfigReader(ABC):
    @staticmethod
    @abstractmethod
    def read(conf_obj):
        """Read configuration"""


class DefaultConfig(IConfigReader):
    """Hardcoded default configuration"""
    @staticmethod
    def read(conf_obj):
        default_configuration = """{
            "gnc_book" : {
                "filetype": "xml",
                "filename": "ttt"
            },
            "accounts": [
                {
                    "Depotkonto": [
                        "Aktiva:Barvermögen:MLP:Abwicklungskonto",
                        "Aktiva:Barvermögen:Deutsche Bank:Depotkonto"
                    ]
                },
                {
                    "Tagesgeld": [
                        "Aktiva:Barvermögen:MLP:Tagesgeldkonto"
                    ]
                }
            ],
            "portfolios": [
                {
                    "Depot": [
                        "Aktiva:Investments:Wertpapierdepot"
                    ]
                }    
            ],
            "interest": [
                "Erträge:Zinsen:MLP Konten",
                "Erträge:Zinsen:Tagesgeld MLP"
            ],
            "fees": [
                "Aufwendungen:Bankgebühren:MLP:Wertpapierdepot",
                "Aufwendungen:Bankgebühren:MLP:Konten",
                "Aufwendungen:Bankgebühren:Deutsche Bank:Depot DB"
            ],
            "tax": [
                "Aufwendungen:Steuern:Kapitalertragssteuer",
                "Aufwendungen:Steuern:Solidaritätszuschlag",
                "Aufwendungen:Steuern:Quellensteuer"
            ],
            "dividends": [
                "Erträge:Dividende:Wertpapierdepot"
            ]
        }"""

        conf_json = json.loads(default_configuration)


class ConfigurationLoader:
    @staticmethod
    def read():

        return DefaultConfig.read(conf_obj)


# ini = {
#     "gnc_file": "Haushalt_sq3.gnucash",
#     "due_date": "2012-01-01"
# }

# def load_ini():
#     if len(sys.argv) > 1:
#         ini = sys.argv[1]
#     else:
#         ini = 'pc.json'
#
#     with open(ini, 'r') as f:
#         return json.load(f)
#
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
