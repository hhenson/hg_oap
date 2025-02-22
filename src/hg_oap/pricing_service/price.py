from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeVar

from hg_oap.pricing_service.timed_value import TimedValue
from hg_oap.units import UnitConversionContext, Unit, Quantity
from hgraph import TSB, COMPOUND_SCALAR
from hgraph.stream.stream import Stream

__all__ = (
    "PriceType",
    "Price",
    "PRICE",
)


class PriceType(Enum):
    NONE = -1
    TRADE = 0
    MID = 1
    BID = 2
    ASK = 3
    CLOSE = 4
    FIXING = 5
    IMPLIED = 6
    MODEL = 7
    FIXED = 8
    SETTLE = 9


@dataclass(frozen=True)
class Price(TimedValue, UnitConversionContext):
    """
    Price represents a single price for an instrument at a given time along with metadata to describe it
    such as units, its type and status
    Optionally a size may be associated with the price (e.g. for last trade price)
    """
    currency_unit: Unit
    unit: Unit
    price_type: PriceType
    origin: str
    size: float

    @property
    def unit_conversion_factors(self) -> tuple[Quantity]:
        return (self.val * (self.currency_unit / self.unit),)


# A PRICE as published by the pricing service is a TSB of a Stream of CompoundScalars (prices of various types)
PRICE = TypeVar("PRICE", bound=TSB[Stream[COMPOUND_SCALAR]])
