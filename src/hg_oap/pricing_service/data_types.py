from dataclasses import dataclass
from datetime import date
from typing import Type

from hg_oap.instruments.instrument import Instrument
from hgraph import CompoundScalar


@dataclass(frozen=True, kw_only=True, repr=False)
class PriceOpts(CompoundScalar):

    def __repr__(self) -> str:
        return ""


@dataclass(frozen=True, kw_only=True)
class PricingModel(CompoundScalar):
    """
    Pricing model configures settings for an instance of a pricing branch.
    It is subclassed for different pricing functions and dispatched to the correct implementation.
    """


@dataclass(frozen=True)
class PricingRequest(CompoundScalar):
    """
    Request for a price.  The parameter to the pricing service
    """
    instrument: str
    opts: PriceOpts


@dataclass(frozen=True)
class PriceTraits:
    """
    Price Traits determine which pricing model will be used based on the table in the PricingRegimeContext
    Subclass to provide specific traits to match against specific instruments, adding attributes and modifying
    the score method.  Use the traits in the PricingRegimeContext mappings
    """
    pricing_opts_type: Type[PriceOpts]
    instrument_type: Type[Instrument]

    def score(self,
              instrument: Instrument,
              instrument_type: Type[Instrument],
              opts_type: Type[PriceOpts],
              business_date: date) -> int:
        # Calculate a 'score' for matching the traits to the given instrument
        if self.instrument_type is not instrument_type or self.pricing_opts_type is not opts_type:
            return -1
        else:
            return 1
