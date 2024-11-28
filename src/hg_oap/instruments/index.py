from dataclasses import dataclass

from hg_oap.instruments.instrument import Instrument
from hg_oap.utils import SELF

__all__ = ("Index",)


# TODO - an Index should perhaps not be an Instrument.  It is Priceable but not Tradable

@dataclass(frozen=True, kw_only=True)
class Index(Instrument):
    SELF: "Index" = SELF
    """
    An Index is a reference value typically used as an underlyer to an instrument.  It cannot be traded directly and
    it is not possible to hold a position in an Index, but it can be priced.
    Examples:  S&P500, Daily Power Fixings.
    """
    symbol: str
