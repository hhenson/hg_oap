import dataclasses
from datetime import date
from typing import Type, Tuple

from hg_oap.instruments.instrument import Instrument
from hg_oap.pricing_service import PriceOpts, PricingModel, PriceTraits, PricingRegimeContext
from hgraph import compute_node, TS, CompoundScalar, CONTEXT, REQUIRED

__all__ = ("choose_pricing_model",)


@compute_node
def choose_pricing_model(instrument: TS[Instrument],
                         instrument_type: TS[Type[Instrument]],
                         opts_type: TS[Type[PriceOpts]],
                         pricing_regime_context: PricingRegimeContext,
                         path: str,
                         business_date: CONTEXT[TS[date]] = REQUIRED['business_date']) -> TS[PricingModel]:

    instrument = instrument.value
    business_date = business_date.value
    opts_type = opts_type.value
    instrument_type = instrument_type.value

    best_score = -1
    best_model = None
    for i_type, o_type in _types(instrument_type, opts_type):
        for traits, model in pricing_regime_context.pricing_model_mapping.items():
            score = traits.score(instrument, i_type, o_type, business_date)
            if score > best_score:
                best_model = model
                best_score = score

    if best_model is None:
        from hg_oap.pricing_service.error_pricing_model import ErrorPricingModel
        traits = {}
        # TODO - this should be the specific PriceTraits subclass for the instrument
        for field in dataclasses.fields(PriceTraits):
            try:
                trait = getattr(instrument, field.name, None)
                if trait is not None:
                    try:
                        trait = trait()
                    except:
                        try:
                            trait = trait(BUSINESS_DATE=business_date)
                        except:
                            ...
                    traits[field.name] = trait
            except:
                ...
        best_model = ErrorPricingModel(traits=traits)

    return best_model


def _types(instrument_type: Type[Instrument], opts_type: Type[PriceOpts]) -> Tuple[Type[Instrument], Type[PriceOpts]]:
    i_type = instrument_type
    o_type = opts_type
    while o_type is not CompoundScalar:
        while i_type is not CompoundScalar:
            yield i_type, o_type
            i_type = i_type.__mro__[1]
        o_type = o_type.__mro__[1]
