from dataclasses import dataclass

from hg_oap.instruments.future import Future
from hg_oap.instruments.instrument import Instrument
from hg_oap.units import Unit, Quantity
from hg_oap.utils import SELF

__all__ = ("FutureSpread",)


@dataclass(frozen=True, kw_only=True)
class FutureSpread(Instrument):
    SELF: "FutureSpread" = SELF

    """
    A spread between two fixed futures generally with different underlying instruments.  The weight of the
    long future is fixed at 1.0 and that of the short future is -1.0 - i.e. a long position in a future 
    spread is economically equivalent to buying the long leg and selling the short leg.
    """
    symbol: str = lambda self: f"{self.long.symbol}-{self.short.symbol}"
    name: str = lambda self: f"{self.long.name}-{self.short.name}"

    currency_unit: Unit = SELF.long.currency_unit
    unit: Unit = SELF.long.unit
    tick_size: Quantity[float] = SELF.long.tick_size

    long: Future
    short: Future
