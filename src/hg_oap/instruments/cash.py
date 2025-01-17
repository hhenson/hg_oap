from dataclasses import dataclass

from hg_oap.assets.currency import Currency
from hg_oap.instruments.instrument import Instrument
from hg_oap.units import Unit, Quantity
from hg_oap.utils import SELF


__all__ = ("Cash",)


@dataclass(frozen=True)
class Cash(Instrument):
    currency: Currency

    currency_unit: Unit = SELF.currency.unit
    unit: Unit = SELF.currency.unit

    unit_conversion_factors: tuple[Quantity, ...] = ()


