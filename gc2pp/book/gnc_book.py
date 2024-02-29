from __future__ import annotations

import datetime
from abc import ABC, abstractmethod
from decimal import Decimal


class GncCommodity(ABC):
    @property
    @abstractmethod
    def space(self):
        pass

    @property
    @abstractmethod
    def symbol(self):
        pass

    @property
    @abstractmethod
    def name(self):
        pass

    @property
    @abstractmethod
    def xcode(self):
        pass


class GncAccount(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def fullname(self) -> str:
        pass

    @property
    @abstractmethod
    def type(self) -> str:
        pass

    @property
    @abstractmethod
    def commodity(self) -> GncCommodity:
        pass

    @property
    @abstractmethod
    def children(self) -> list[GncAccount]:
        pass

    @property
    @abstractmethod
    def splits(self) -> list[GncSplit]:
        pass


class GncTransaction(ABC):
    @property
    @abstractmethod
    def splits(self) -> list[GncSplit]:
        pass

    @property
    @abstractmethod
    def post_date(self) -> datetime.datetime:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass


class GncSplit(ABC):
    @property
    @abstractmethod
    def transaction(self) -> GncTransaction:
        pass

    @property
    @abstractmethod
    def account(self) -> GncAccount:
        pass

    @property
    @abstractmethod
    def value(self) -> Decimal:
        pass

    @property
    @abstractmethod
    def quantity(self) -> Decimal:
        pass


class GncBook(ABC):
    """
    The GncBook defines general interface to GnuCash data.
    """

    @property
    @abstractmethod
    def commodities(self) -> list[GncCommodity]:
        pass

    @property
    @abstractmethod
    def accounts(self) -> list[GncAccount]:
        pass

    @abstractmethod
    def find_account_by_name(self, fullname: str) -> GncAccount:
        pass
