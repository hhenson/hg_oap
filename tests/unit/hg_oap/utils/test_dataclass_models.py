from dataclasses import dataclass, fields, FrozenInstanceError, is_dataclass

import pytest

from hg_oap.assets.asset import Asset
from hg_oap.instrument_data_service.instrument_data_service import InstrumentData
from hg_oap.instruments.future import (
    FutureContractSeries,
    FutureContractSpec,
    Settlement,
)
from hg_oap.instruments.instrument import Instrument, InstrumentId
from hg_oap.orders.order import Fill, OriginatorInfo
from hg_oap.orders.order_request_response_events import (
    OrderEvent,
    OrderRequest,
    OrderResponse,
)
from hg_oap.orders.order_type import OrderType
from hg_oap.pricing.price import Price as MarketPrice
from hg_oap.pricing_service.data_types import (
    PriceOpts,
    PriceTraits,
    PricingModel,
    PricingRequest,
)
from hg_oap.pricing_service.price import Price as ServicePrice
from hg_oap.pricing_service.price_mesh_ui import PriceUIView
from hg_oap.pricing_service.timed_value import TimedValue
from hg_oap.stream import Stream
from hg_oap.units import Dimension, Quantity, Unit
from hgraph import CompoundScalar, TSB
from hgraph.reflection import fields as time_series_fields


PYTHON_OWNED_MODELS = (
    Dimension,
    Unit,
    Quantity,
    Asset,
    InstrumentId,
    Instrument,
    Settlement,
    FutureContractSpec,
    FutureContractSeries,
    OriginatorInfo,
    Fill,
    OrderType,
    OrderRequest,
    OrderResponse,
    OrderEvent,
    InstrumentData,
    MarketPrice,
    TimedValue,
    PriceOpts,
    PricingModel,
    PricingRequest,
    PriceTraits,
    ServicePrice,
    PriceUIView,
)


def test_domain_models_are_python_owned_dataclasses():
    for model in PYTHON_OWNED_MODELS:
        assert is_dataclass(model), model
        assert not issubclass(model, CompoundScalar), model


def test_domain_models_are_frozen():
    for model in PYTHON_OWNED_MODELS:
        instance = object.__new__(model)
        try:
            instance._frozen_probe = True
        except FrozenInstanceError:
            pass
        else:
            raise AssertionError(f"{model.__qualname__} must be a frozen dataclass")


def test_expression_fields_are_not_stored_dataclass_fields():
    assert [field.name for field in fields(FutureContractSpec)] == [
        "exchange_mic",
        "symbol",
        "underlying",
        "contract_size",
        "currency",
        "trading_calendar",
        "settlement",
        "quotation_currency_unit",
        "quotation_unit",
        "tick_size",
    ]


def test_stream_supports_python_owned_dataclass_payloads():
    assert set(time_series_fields(TSB[Stream[InstrumentData]])) == {
        "status",
        "status_msg",
        "instrument",
    }
    assert set(time_series_fields(TSB[Stream[ServicePrice]])) == {
        "status",
        "status_msg",
        "val",
        "timestamp",
        "currency_unit",
        "unit",
        "price_type",
        "origin",
        "size",
    }


def test_stream_rejects_mutable_dataclass_payloads():
    @dataclass
    class MutablePayload:
        value: int

    with pytest.raises(TypeError, match="must be frozen"):
        Stream[MutablePayload]
