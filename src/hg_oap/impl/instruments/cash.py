from enum import Enum

from hg_oap.impl.assets.currency import Currencies
from hg_oap.instruments.cash import Cash


class CashInstruments(Enum):
    EUR = Cash(symbol="EUR", currency=Currencies.EUR)
    GBP = Cash(symbol="GBP", currency=Currencies.GBP)
    USD = Cash(symbol="USD", currency=Currencies.USD)
