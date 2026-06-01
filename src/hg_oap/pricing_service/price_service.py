import logging
from typing import Type

from hg_oap.instrument_data_service.instrument_data_service import instrument_by_name
from hg_oap.instruments.instrument import Instrument
from hg_oap.pricing_service import PricingRegimeContext, delayed_log, combine_errors, PriceType, PriceExplain, \
    PriceExplainLeaf
from hg_oap.pricing_service.business_date import current_business_date
from hg_oap.pricing_service.data_types import PriceOpts, PricingModel, PricingRequest
from hg_oap.pricing_service.price import PRICE
from hg_oap.pricing_service.price_mesh_ui import create_price_view, price_row_key, publish_price_row, PriceUIView
from hg_oap.pricing_service.pricing_model_choice import choose_pricing_model
from hg_oap.units import Unit
from hg_oap.utils import replace
from hgraph import subscription_service, TS, graph, service_impl, TSS, TSD, AUTO_RESOLVE, dispatch, type_, \
    COMPOUND_SCALAR, mesh_, operator, combine, if_then_else, try_except, dedup, compute_node, log_, str_, \
    CompoundScalar, switch_, valid, or_, TSB, default, getattr_, SCALAR, sink_node, LOGGER, if_
from hgraph.stream.stream import StreamStatus

__all__ = ("subscribe_price", "subscribe_price_by_name", "price_service", "pricing_model", "pricing_service_impl")


@operator
def subscribe_price(request: TS[CompoundScalar]) -> PRICE:
    ...


@graph(overloads=subscribe_price)
def subscribe_price_by_request(
    request: TS[PricingRequest], path: str = "instrument_price", price_type: Type[PRICE] = AUTO_RESOLVE
) -> PRICE:
    if pricing_mesh := mesh_(f"pricing_service_{path}[{str(price_type)}]"):
        return pricing_mesh[request]
    else:
        return price_service[price_type](request, path=path)


@graph(overloads=subscribe_price)
def subscribe_price_by_name(
    request: TS[str], path: str = "instrument_price", price_type: Type[PRICE] = AUTO_RESOLVE
) -> PRICE:
    pricing_request = combine[TS[PricingRequest]](instrument=request, opts=PriceOpts())
    return subscribe_price(pricing_request, path, price_type)


@subscription_service
def price_service(request: TS[PricingRequest], path: str) -> PRICE:
    ...


@dispatch
@operator
def pricing_model(instrument: TS[Instrument], opts: TS[PriceOpts], model: TS[PricingModel]) -> PRICE:
    """
    The pricing model operator implements the logic of pricing the instrument given the pricing model and options
    provided. Overloads will specify what model they implement as the type of the `model` argument and can further
    specialise on the instrument and options type and also on the PRICE type parameter.
    """

DEFAULT_EXPLAIN = PriceExplainLeaf(symbol="<unset>", narrative="No price explanation given")

@service_impl(interfaces=(price_service,))
def pricing_service_impl(
    request: TSS[PricingRequest],
    path: str,
    pricing_regime_context: PricingRegimeContext,
    price_type: Type[PRICE] = AUTO_RESOLVE,
    publish_to_ui: bool = True
) -> TSD[PricingRequest, PRICE]:

    with pricing_regime_context:

        @graph
        def _invoke_pricing_model(key: TS[PricingRequest]) -> price_type:
            symbol = key.instrument
            opts = key.opts
            ref_data = instrument_by_name(symbol)
            instrument = ref_data.instrument
            ref_data_error = ref_data.status_msg
            delayed_log(symbol, ref_data_error)

            model = choose_pricing_model(
                instrument,
                type_[COMPOUND_SCALAR: Instrument](instrument),
                type_[COMPOUND_SCALAR: PriceOpts](opts),
                pricing_regime_context,
                current_business_date(),
                path
            )
            pricing_model_dispatch = extract_pricing_model_dispatch(pricing_regime_context, price_type)

            price_result = try_except(pricing_model_dispatch, instrument, opts, model)
            price = switch_(
                valid(price_result.exception),
                {
                    True: _exception_price,
                    False: _no_exception_price
                },
                symbol=symbol,
                model=model,
                ref_data_error=ref_data_error,
                price=price_result.out,
                exception=str_(price_result.exception),
                price_type=price_type,
                opts=opts,
                publish_to_ui=publish_to_ui,
                path=path,
            )
            log_price_with_no_val_but_good_status(path, key, price)
            price_explain = default(price.price_explain, DEFAULT_EXPLAIN)
            defaulted_price = price.copy_with(
                origin=default(price.origin, "pricing"),
                unit=default(price.unit, getattr_[SCALAR: Unit](instrument, "unit")),
                currency_unit=default(price.currency_unit, getattr_[SCALAR: Unit](instrument, "currency_unit")),
                price_type=default(price.price_type, PriceType.NONE),
                price_explain=add_request_to_explain(price_explain, key),
            )
            return if_(valid(price.status), defaulted_price).true

        return mesh_(_invoke_pricing_model, __keys__=request, __name__=f"pricing_service_{path}[{str(price_type)}]")


@compute_node
def add_request_to_explain(price_explain: TS[PriceExplain], pricing_request: TS[PricingRequest]) -> TS[PriceExplain]:
    # TODO - need a copy_with for TS[CompoundScalar]
    pricing_request = pricing_request.value
    return replace(
        price_explain.value,
        symbol=pricing_request.instrument,
        opts=pricing_request.opts,
        pricing_request=pricing_request
    )


@sink_node
def log_price_with_no_val_but_good_status(path: str, request: TS[PricingRequest], price: PRICE, log: LOGGER = None):
    if not price.val.valid and price.status.value is StreamStatus.OK:
        request = request.value
        if request.opts == PriceOpts():
            request = request.instrument
        log.error(f"{path} price for {request} ticked with good status but no price: {price.value}")


@graph
def _exception_price(
    symbol: TS[str],
    model: TS[PricingModel],
    ref_data_error: TS[str],
    price: PRICE,
    exception: TS[str],
    price_type: Type[PRICE],
    opts: TS[PriceOpts],
    publish_to_ui: bool,
    path: str,
) -> PRICE:
    log_(
        "Exception attempting to execute {} on {} for {}, price type {}:\n{}",
        type_(model).name,
        path,
        symbol,
        price_type,
        exception,
        level=logging.ERROR
    )
    if publish_to_ui:
        view = combine[TSB[PriceUIView]](status=exception)
        publish_price_row(price_row_key(symbol, model, opts), view)
    return error_return(symbol, exception, price, StreamStatus.FATAL, price_type)


@graph
def _no_exception_price(
    symbol: TS[str],
    model: TS[PricingModel],
    ref_data_error: TS[str],
    price: PRICE,
    exception: TS[str],
    price_type: Type[PRICE],
    opts: TS[PriceOpts],
    publish_to_ui: bool,
    path: str,
) -> PRICE:
    error = dedup(combine_errors(symbol, ref_data_error, price.status_msg))
    no_good_price_yet = or_(price.status >= StreamStatus.WAITING, ref_data_error != "")
    error_symbol = if_(no_good_price_yet, symbol).true
    price = if_then_else(
        no_good_price_yet,
        error_return(error_symbol, error, price, price.status, price_type),
        price
    )
    if publish_to_ui:
        view = create_price_view(price, model)
        publish_price_row(price_row_key(symbol, model, opts), view)
    return price


def extract_pricing_model_dispatch(pricing_regime_context, price_type):
    from hg_oap.pricing_service.error_pricing_model import ErrorPricingModel
    models_in_use = {m.__class__ for m in pricing_regime_context.pricing_model_mapping.values()}
    models_in_use.add(ErrorPricingModel)

    @dispatch
    @operator
    def _pricing_model(instrument: TS[Instrument], opts: TS[PriceOpts], model: TS[PricingModel]) -> PRICE:
        ...

    for o, r in pricing_model.overload_list.overloads:
        if any(issubclass(m, o.signature.input_types["model"].value_scalar_tp.py_type) for m in models_in_use):
            _pricing_model.overload(o)
    return _pricing_model[price_type]


@compute_node(valid=("symbol",))
def error_return(
    symbol: TS[str],
    error: TS[str],
    price: PRICE,
    status: TS[StreamStatus],
    price_type: Type[PRICE]
) -> PRICE:
    error = error.value or f"No price yet for {symbol.value}"
    status = status.value or StreamStatus.WAITING
    return {
        "status": status if status.value > StreamStatus.STALE.value else StreamStatus.ERROR,
        "status_msg": error,
        "origin": price.origin.value,
        "unit": price.unit.value,
        "currency_unit": price.currency_unit.value,
        "timestamp": price.timestamp.value,
        "price_explain": price.price_explain.value
    }
