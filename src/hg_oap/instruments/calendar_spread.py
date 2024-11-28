from dataclasses import dataclass

from hg_oap.instruments.future import Future
from hg_oap.instruments.instrument import Instrument
from hg_oap.units import Quantity, Unit
from hg_oap.utils import SELF


@dataclass(frozen=True, kw_only=True)
class CalendarSpread(Instrument):
    SELF: "CalendarSpread" = SELF

    """
    A calendar spread between two fixed futures on the same underlying asset for different tenors
    (Note: it is possible that the near and far legs have different contract series, for example for 3rd Sep vs 3rd Oct
     or summer vs winter)
    The weight of the near leg is fixed at 1.0 and that of the far leg at -1.0 - i.e. a long position in a calendar 
    spread is economically equivalent to buying the near leg and selling the far
    """
    symbol: str = lambda self: f"{self.near.symbol}-{self.far.symbol}"
    name: str = lambda self: f"{self.near.name}-{self.far.name}"

    currency_unit: Unit = SELF.near.currency_unit
    unit: Unit = SELF.near.unit
    tick_size: Quantity = SELF.near.tick_size

    near: Future
    far: Future
