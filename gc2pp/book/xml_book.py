from __future__ import annotations
from functools import lru_cache

import datetime
from decimal import Decimal
from gnucashxml import gnucashxml
from book import GncBook, GncCommodity, GncAccount, GncSplit, GncTransaction


class XMLCommodity(GncCommodity):
    _commodity_index = {}

    def __init__(self, gnc_cmdty: gnucashxml.Commodity):
        self._commodity = gnc_cmdty
        self._commodity_index.setdefault(gnc_cmdty, self)

    @property
    def space(self) -> str:
        return self._commodity.space

    @property
    def symbol(self) -> str:
        return self._commodity.symbol

    @property
    def name(self) -> str:
        return self._commodity.name

    @property
    def xcode(self) -> str:
        return self._commodity.xcode

    @classmethod
    def get_commodity(cls, gnc_cmdty) -> XMLCommodity:
        return cls._commodity_index.get(gnc_cmdty)


class XMLAccount(GncAccount):
    _account_index = {}

    def __init__(self, gnc_act: gnucashxml.Account) -> None:
        self._gnc_act: gnucashxml.Account = gnc_act
        self._account_index.setdefault(gnc_act, self)

    @property
    def name(self):
        return self._gnc_act.name

    @property
    def fullname(self):
        return self._gnc_act.fullname

    @property
    def type(self):
        return self._gnc_act.type

    @property
    def commodity(self) -> GncCommodity:
        return XMLCommodity.get_commodity(self._gnc_act.commodity)

    @property
    def children(self) -> list[GncAccount]:
        return [self.get_account(a) for a in self._gnc_act.children]

    @property
    def splits(self) -> list[GncSplit]:
        return [XMLSplit(a) for a in self._gnc_act.splits]

    @classmethod
    def get_account(cls, gnc_act) -> GncAccount:
        return cls._account_index.get(gnc_act)


@lru_cache()
class XMLSplit(GncSplit):
    def __init__(self, gnc_split: gnucashxml.Split):
        self._gnc_split: gnucashxml.Split = gnc_split

    @property
    def transaction(self) -> GncTransaction:
        return XMLTransaction(self._gnc_split.transaction)

    @property
    def account(self) -> GncAccount:
        return XMLAccount.get_account(self._gnc_split.account)

    @property
    def value(self) -> Decimal:
        return self._gnc_split.value

    @property
    def quantity(self) -> Decimal:
        return self._gnc_split.quantity


@lru_cache()
class XMLTransaction(GncTransaction):
    def __init__(self, gnc_trn: gnucashxml.Transaction):
        self._gnc_trn: gnucashxml.Transaction = gnc_trn

    @property
    def splits(self) -> list[GncSplit]:
        return [XMLSplit(a) for a in self._gnc_trn.splits]

    @property
    def post_date(self) -> datetime.datetime:
        return self._gnc_trn.date

    @property
    def description(self) -> str:
        return self._gnc_trn.description


class XMLBook(GncBook):
    """
    The XMLAdapter reads GNUCash XML files and makes it compatible with the gncBook
    interface via composition.
    """

    def __init__(self, xml_filename: str) -> None:
        self._book: gnucashxml.book = gnucashxml.load(xml_filename)
        self._commodities = [XMLCommodity(c) for c in self._book.commodities]
        self._accounts = [XMLAccount(a) for a in self._book.accounts]

    @property
    def commodities(self) -> list[GncCommodity]:
        return self._commodities

    @property
    def accounts(self) -> list[GncAccount]:
        return self._accounts
