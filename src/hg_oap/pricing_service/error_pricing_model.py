from dataclasses import dataclass
from typing import Type

from frozendict import frozendict

from hg_oap.instruments.instrument import Instrument
from hg_oap.pricing_service import PRICE, PriceOpts, PricingModel, PriceType
from hg_oap.pricing_service.price_service import pricing_model
from hg_oap.units import Unit
from hgraph import graph, TS, AUTO_RESOLVE, combine, format_, type_, getattr_, SCALAR, last_modified_time
from hgraph.stream.stream import StreamStatus

__all__ = ("pricing_model_error", "ErrorPricingModel")


@dataclass(frozen=True, kw_only=True)
class ErrorPricingModel(PricingModel):
    traits: frozendict[str, object]


@graph(overloads=pricing_model)
def pricing_model_error(instrument: TS[Instrument],
                        opts: TS[PriceOpts],
                        model: TS[ErrorPricingModel],
                        price_type: Type[PRICE] = AUTO_RESOLVE) -> PRICE:
    status_msg = format_("No model for {}, {}  ({}, traits {})",
                         instrument.symbol,
                         type_(opts).name,
                         type_(instrument).name,
                         model.traits)
    return combine[price_type](status=StreamStatus.ERROR,
                               status_msg=status_msg,
                               unit=getattr_[SCALAR: Unit](instrument, "unit"),
                               currency_unit=getattr_[SCALAR: Unit](instrument, "currency_unit"),
                               origin="error",
                               price_type=PriceType.NONE,
                               timestamp=last_modified_time(status_msg))
