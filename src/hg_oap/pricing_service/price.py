from dataclasses import dataclass
from enum import auto, Enum
from typing import TypeVar

from frozendict import frozendict

from hg_oap.pricing_service import PriceType
from hg_oap.pricing_service.price_explain import PriceExplain
from hg_oap.pricing_service.timed_value import TimedValue
from hg_oap.units import UnitConversionContext, Unit, Quantity
from hgraph import TSB, COMPOUND_SCALAR
from hgraph.stream.stream import Stream

__all__ = ("Price", "PRICE", "PriceAttribute")


# TODO - extend the behaviour of extended price attributes using enum values - e.g. how to combine them
class PriceAttribute(Enum):
    BID = auto()
    ASK = auto()

    # Greeks
    DELTA = auto()
    IMPLIED_VOL = auto()


@dataclass(frozen=True, kw_only=True)
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
    price_explain: PriceExplain

    # Optional extended attributes - e.g. greeks, bid/ask etc
    price_attributes: frozendict[PriceAttribute, object]

    @property
    def unit_conversion_factors(self) -> tuple[Quantity, ...]:
        return (self.val * (self.currency_unit / self.unit),)


# A PRICE as published by the pricing service is a TSB of a Stream of CompoundScalars (prices of various types)
PRICE = TypeVar("PRICE", bound=TSB[Stream[COMPOUND_SCALAR]])
