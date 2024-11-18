from dataclasses import dataclass

from hg_oap.assets.currency import Currency
from hg_oap.instruments.instrument import Instrument
from hg_oap.units import Unit
from hg_oap.utils import SELF

__all__ = ("FXSpot", "FXPoints", "FXForward")


@dataclass(frozen=True, kw_only=True)
class FXSpot(Instrument):
    SELF: "FXSpot" = SELF

    base: Currency
    quote: Currency

    currency_unit: Unit = SELF.quote.unit
    unit: Unit = SELF.base.unit

    currency_pair: str = lambda self: f"{self.base.symbol}{self.quote.symbol}"


@dataclass(frozen=True, kw_only=True)
class FXPoints(Instrument):
    SELF: "FXPoints" = SELF

    base: Currency
    quote: Currency
    tenor: str  # SPOT, ON, SN, 1W, 2W, 3W, 4W, 1M... 1Y etc

    currency_unit: Unit = SELF.quote.unit
    unit: Unit = SELF.base.unit

    currency_pair: str = lambda self: f"{self.base.symbol}{self.quote.symbol}"


@dataclass(frozen=True, kw_only=True)
class FXForward(Instrument):
    SELF: "FXForward" = SELF

    base: Currency
    quote: Currency
    tenor: str  # SPOT, ON, SN, 1W, 2W, 3W, 4W, 1M... 1Y etc

    currency_unit: Unit = SELF.quote.unit
    unit: Unit = SELF.base.unit

    currency_pair: str = lambda self: f"{self.base.symbol}{self.quote.symbol}"
