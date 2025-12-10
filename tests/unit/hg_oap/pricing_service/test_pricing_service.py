from dataclasses import dataclass
from datetime import date
from typing import Type

from hg_oap.assets.asset import PhysicalAsset
from hg_oap.impl.assets.currency import Currencies
from hg_oap.dates import WeekendCalendar, months
from hg_oap.instrument_data_service.instrument_data_service import instrument_by_name, InstrumentData
from hg_oap.instruments.calendar_spread import CalendarSpread
from hg_oap.instruments.future import Future, FutureContractSeries, FutureContractSpec, Settlement, SettlementMethod
from hg_oap.instruments.instrument import Instrument
from hg_oap.instruments.physical import PhysicalCommodity
from hg_oap.pricing_service import PriceTraits, PricingRegimeContext, PriceOpts, PRICE, Price, PricingModel, \
    PriceType
from hg_oap.pricing_service.price_service import pricing_service_impl, subscribe_price, pricing_model
from hg_oap.units import Unit, Quantity
from hg_oap.units.default_unit_system import U
from hgraph import graph, TS, const, register_service, TSB, WiringGraphContext, AUTO_RESOLVE, combine, MIN_DT, \
    getattr_, SCALAR, service_impl, TSS, TSD, map_, compute_node
from hgraph.stream.stream import Stream, StreamStatus
from hgraph.test import eval_node

"""
Sample pricing models.  The PricingModel subclass may define parameters which govern the behaviour of the pricing model.
The PricingModel and the pricing_model are linked using the overload of pricing_model.
"""
@dataclass(frozen=True, kw_only=True)
class CalendarSpreadPricingModel(PricingModel):
    ...


@graph(overloads=pricing_model, requires=lambda m: m[PRICE].py_type == TSB[Stream[Price]])
def calendar_spread_pricing_model(instrument: TS[CalendarSpread],
                                  opts: TS[PriceOpts],
                                  model: TS[CalendarSpreadPricingModel],
                                  price_type: Type[PRICE] = AUTO_RESOLVE) -> PRICE:

    price_near = subscribe_price[price_type](instrument.near.symbol)
    price_far = subscribe_price[price_type](instrument.far.symbol)
    return (price_near - price_far).copy_with(origin="calculated", price_type=PriceType.MODEL)


@dataclass(frozen=True, kw_only=True)
class MarketDataPricingModel(PricingModel):
    ...


@graph(overloads=pricing_model, requires=lambda m: m[PRICE].py_type == TSB[Stream[Price]])
def market_data_pricing_model(instrument: TS[Future],
                              opts: TS[PriceOpts],
                              model: TS[MarketDataPricingModel],
                              price_type: Type[PRICE] = AUTO_RESOLVE) -> PRICE:
    return combine[TSB[Stream[Price]]](status=StreamStatus.OK,
                                       status_msg="",
                                       val=101.0,
                                       timestamp=MIN_DT,
                                       currency_unit=getattr_[SCALAR: Unit](instrument, "currency_unit"),
                                       unit=getattr_[SCALAR: Unit](instrument, "unit"),
                                       price_type=PriceType.MID,
                                       origin="some market data source")

class Gas(PhysicalAsset):
    ...


"""
Test artefact implementation of the instrument_by_name service.
The pricing service assumes that instrument symbols (names) are unique.
The implementation of instrument_by_name must provide the Instrument definition (and a status/status message).
"""
@service_impl(interfaces=instrument_by_name)
def instrument_by_name_impl(key: TSS[str]) -> TSD[str, TSB[Stream[InstrumentData]]]:
    @compute_node
    def inst(symbol: TS[str]) -> TS[Instrument]:
        symbol = symbol.value

        spec = FutureContractSpec(
            exchange_mic="ICE",
            symbol="ICE_TFM",
            underlying=PhysicalCommodity(symbol="DUTCH_GAS_INST",
                                         asset=Gas(symbol="DUTCH_GAS", name="Dutch Natural Gas")),
            contract_size=Quantity(1.0, U.MW),
            currency=Currencies.EUR,
            trading_calendar=WeekendCalendar(),
            settlement=Settlement(method=SettlementMethod.Financial),
            quotation_currency_unit=U.EUR,
            quotation_unit=U.MWh,
            tick_size=Quantity(1.0, U.MWh))

        future_series = FutureContractSeries(
            spec=spec,
            name="M",
            symbol_expr=lambda future: f"f{future.contract_base_date.month}",
            frequency=months,
            first_trading_date=None,
            last_trading_date=None,
            last_trading_time=None,
            first_delivery_date=None,
            last_delivery_date=None,
            expiry=None)
        f1 = Future(symbol=symbol, series=future_series, contract_base_date=date(2024, 1, 1))
        f2 = Future(symbol=symbol, series=future_series, contract_base_date=date(2024, 2, 1))
        if symbol == "f1":
            return f1
        elif symbol == "f2":
            return f2
        elif symbol == "f1-f2":
            return CalendarSpread(near=f1, far=f2)
        assert False, f"Unrecognised symbol: {symbol}"

    @graph
    def g(key: TS[str]) -> TSB[Stream[InstrumentData]]:
        return combine[TSB[Stream[InstrumentData]]](instrument=inst(key),
                                                    status=StreamStatus.OK,
                                                    status_msg="")
    return map_(g, __keys__=key)


"""
PriceTraits implement scoring filter attributes against instrument attributes.  
They are part of the pricing regime context mappings.
"""
@dataclass(frozen=True)
class PriceTraitsFuture(PriceTraits):
    instrument_type: Type[Instrument] = Future
    unit: Unit = None

    def score(self,
              instrument: Instrument,
              instrument_type: Type[Instrument],
              opts_type: Type[PriceOpts],
              business_date: date) -> int:
        if super().score(instrument, instrument_type, opts_type, business_date) < 0:
            return -1

        score = 0
        if self.unit is not None:
            if self.unit is instrument.unit:
                score += 1
            else:
                return -1
        return score


def test_pricing_service():

    @graph
    def g(inst: TS[str]) -> PRICE:
        with const(date(2024, 11, 22)) as business_date:
            register_service("instrument", instrument_by_name_impl)

            prc = PricingRegimeContext(
                name='test',
                pricing_model_mapping={
                    PriceTraits(PriceOpts, CalendarSpread): CalendarSpreadPricingModel(),
                    PriceTraitsFuture(PriceOpts, unit=U.MWh): MarketDataPricingModel(),
                })
            register_service(
                "instrument_price", pricing_service_impl, pricing_regime_context=prc, publish_to_ui=False)

            p = subscribe_price[TSB[Stream[Price]]](inst)

            WiringGraphContext.instance().build_services()
            return p

    results = eval_node(g, ["f1-f2"], __elide__=True)
    assert results[-1] == {"currency_unit": U.EUR,
                           "unit": U.MWh,
                           "origin": "calculated",
                           "price_type": PriceType.MODEL,
                           "status": StreamStatus.OK,
                           "status_msg": "",
                           "timestamp": MIN_DT,
                           "val": 0.0}
