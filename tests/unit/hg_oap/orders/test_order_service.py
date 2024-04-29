import pytest
from hgraph import graph, TS, TSB, compute_node, register_service, MIN_TD, SIGNAL
from hgraph.nodes import delay, sample
from hgraph.test import eval_node

from hg_oap.assets.currency import Currencies
from hg_oap.instruments.instrument import Instrument
from hg_oap.orders.order import OrderState, SingleLegOrder, OriginatorInfo, ORDER, Fill
from hg_oap.orders.order_service import order_handler, OrderRequest, OrderResponse, order_client, \
    CreateOrderRequest, OrderHandlerOutput, OrderEvent
from hg_oap.orders.order_type import MarketOrderType
from hg_oap.pricing.price import Price
from hg_oap.units.dimension import PrimaryDimension
from hg_oap.units.quantity import Quantity
from hg_oap.units.unit import Unit, PrimaryUnit
from hg_oap.units.unit_system import UnitSystem


@pytest.fixture
def unit_system() -> UnitSystem:
    with UnitSystem() as U:
        U.trade_unit = PrimaryDimension()
        U.lot = PrimaryUnit(dimension=U.trade_unit)
        yield U

@order_handler
@graph
def simple_handler(
        request: TS[OrderRequest],
        order_state: TSB[OrderState[SingleLegOrder]]
) -> TSB[OrderHandlerOutput]:
    """
    Simple example
    """
    order_response = _accept_request(request)
    delayed_result = delay(order_response, MIN_TD)
    fill_signal = sample(delayed_result, bool)
    fill_event = _fill_order(order_state.confirmed, fill_signal)
    return TSB[OrderHandlerOutput].from_ts(order_response=order_response, order_event=fill_event)


@compute_node
def _accept_request(request: TS[OrderRequest]) -> TS[OrderResponse]:
    return OrderResponse.accept(request.value)


@compute_node(active=("fill",))
def _fill_order(confirmed: TSB[ORDER], fill: SIGNAL) -> TS[OrderEvent]:
    fill = Fill(fill_id="TestFillId", qty=confirmed.remaining_qty.value, notional=Price(1532.5, Currencies.USD.value))
    confirmed = confirmed.value
    return OrderEvent.create_fill(confirmed, fill)


def test_simple_handler(unit_system: UnitSystem):
    @graph
    def g(ts: TS[OrderRequest]) -> TS[OrderResponse]:
        register_service("order.simple_handler", simple_handler)
        return order_client("order.simple_handler", ts)

    requests = [
        OrderRequest.create_request(
            CreateOrderRequest, None, 'Howard', order_id="1",
            order_type=MarketOrderType(instrument=Instrument(symbol="MCU_3M"),
                                       quantity=Quantity[float](qty=1.0, unit=UnitSystem.instance().lot)),
            originator_info=OriginatorInfo(account="account")
        )
    ]
    result = eval_node(g, requests)
    assert result == [
        None, None,
        OrderResponse.accept(requests[0]),
    ]