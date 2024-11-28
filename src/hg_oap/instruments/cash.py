from dataclasses import dataclass
from enum import Enum

from hg_oap.assets.currency import Currency, Currencies
from hg_oap.instruments.instrument import Instrument
from hg_oap.units import Unit, Quantity
from hg_oap.utils import SELF


__all__ = ("Cash", "CashInstruments")


@dataclass(frozen=True)
class Cash(Instrument):
    currency: Currency

    currency_unit: Unit = SELF.currency.unit
    unit: Unit = SELF.currency.unit

    unit_conversion_factors: tuple[Quantity, ...] = ()


class CashInstruments(Enum):
    EUR = Cash(symbol="EUR", currency=Currencies.EUR)
    GBP = Cash(symbol="GBP", currency=Currencies.GBP)
    USD = Cash(symbol="USD", currency=Currencies.USD)
