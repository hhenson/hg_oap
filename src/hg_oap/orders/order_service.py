from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, TypeVar, cast

from frozendict import frozendict
from hgraph import request_reply_service, reference_service, TSD, TS, CompoundScalar, service_impl, feedback, TSB, \
    compute_node, map_, TSB_OUT, HgTSTypeMetaData, STATE
from hgraph.nodes._tuple_operators import unroll

from hg_oap.orders.order import OriginatorInfo, ORDER, OrderState, SingleLegOrder, MultiLegOrder
from hg_oap.orders.order_type import OrderType, MultiLegOrderType, SingleLegOrderType


@reference_service
def order_states(path: str = None) -> TSD[str, TSB[OrderState[ORDER]]]:
    """
    The order states associated to an order end-point.
    """


ORDER_REQUEST = TypeVar('ORDER_REQUEST', bound="OrderRequest")


@dataclass(frozen=True)
class OrderRequest(CompoundScalar):
    order_id: str
    version: int

    # The below is used for sequence validation
    user_id: str  # Who is updating
    prev_version: int  # The previous version
    prev_user_id: str  # The previous user id

    @staticmethod
    def create_request(
            tp: type[ORDER_REQUEST],
            current_request: TSB[ORDER] | None,
            user_id: str,
            **kwargs
    ) -> ORDER_REQUEST:
        current_request = None if current_request is None else current_request.value
        order_id = kwargs.pop('order_id') if current_request is None else current_request.order_id
        prev_version = -1 if current_request is None else current_request.version
        prev_user_id = "" if current_request is None else current_request.user_id
        return tp(
            order_id=order_id,
            version=prev_version + 1,
            user_id=user_id,
            prev_version=prev_version,
            prev_user_id=prev_user_id,
            **kwargs
        )


@dataclass(frozen=True)
class CreateOrderRequest(OrderRequest):
    order_type: OrderType
    originator_info: OriginatorInfo


@dataclass(frozen=True)
class AmendOrderRequest(OrderRequest):
    order_type_details: frozendict[str, Any]
    originator_info_details: frozendict[str, Any]


@dataclass(frozen=True)
class SuspendOrderRequest(OrderRequest):
    suspension_key: str


@dataclass(frozen=True)
class ResumeOrderRequest(OrderRequest):
    suspension_key: str


@dataclass(frozen=True)
class CancelOrderRequest(OrderRequest):
    """
    Cancel an order, use force=True to cancel an order without waiting for
    a response when the order has children or validation logic.
    """
    reason: str
    force: bool = False


@dataclass(frozen=True)
class OrderResponse(CompoundScalar):
    order_id: str
    version: int
    original_request: OrderRequest

    @staticmethod
    def accept(request: OrderRequest) -> "OrderAcceptResponse":
        """Create an accept message"""
        return OrderAcceptResponse(
            order_id=request.order_id,
            version=request.version,
            original_request=request
        )

    @staticmethod
    def reject(request: OrderRequest, reason: str) -> "OrderRejectResponse":
        """Create a reject message"""
        return OrderReject(
            order_id=request.order_id,
            version=request.version,
            original_request=request,
            reason=reason
        )


@dataclass(frozen=True)
class OrderAcceptResponse(OrderResponse):
    """Indicates the request was accepted"""


@dataclass(frozen=True)
class OrderReject(OrderResponse):
    """Indicates the request was rejected, the reason is also provided"""
    reason: str


@request_reply_service
def order_client(path: str, request: TS[OrderRequest]) -> TS[OrderResponse]:
    """
    Order client allows sending order requests to the order service.
    """


def order_handler(fn):
    """
    Wraps a graph / compute_node that is designed to process an order or
    a collection of orders. The handler takes the form:

    @order_handler
    @graph
    def my_order_handler(
        request: TS[OrderRequest],
        order_state: TSB[OrderState[SingleLegOrder]]
        **kwargs
    ) -> TS[OrderResponse]:
        ...

    If the handler is designed to handle multiple orders, the other options
    is to provide a signature as below, in this form all order requests destined
    for this end-point will be provided.

    @order_handler
    @graph
    def my_order_handler(
        request: TSD[str, tuple[OrderRequest,...]],
        order_state: TSD[str, TSB[OrderState[SingleLegOrder]]]
        **kwargs
    ) -> TSD[str, TS[tuple[OrderResponse,...]]]:
        ...

    The result of this is a service impl allows for handling order requests
    providing a validated stream of order requests and the appropriate
    request and confirmed order states.

    To use this, the user would then perform a registration of the handler
    as follows:

    register_service("orders.my_end_point", my_order_handler, **my_order_handler_kwargs)

    NOTE: The order_state will tick when the response is returned, so generally this should not be in the active
          set as it will cause the code to be re-evaluated the engine cycle after the node is completed.
    """
    # determine type or order state we are looking for based on the wrapped code.
    from hgraph import PythonWiringNodeClass
    signature = cast(PythonWiringNodeClass, fn).signature
    needs_map: bool = isinstance(signature.input_types['request'], HgTSTypeMetaData)
    if needs_map:
        bundle_tp = signature.input_types['order_state']
    else:
        bundle_tp = signature.input_types['order_state'].value_tp

    order_state_tp = bundle_tp.bundle_schema_tp.meta_data_schema['requested'].bundle_schema_tp.py_type
    assert order_state_tp in (SingleLegOrder, MultiLegOrder), \
        "Expect this to be either a SingleLegOrder or MultiLegOrder"

    @service_impl(interfaces=(order_states, order_client))
    def _order_handler_impl(path: str):
        order_responses_fb = feedback(TSD[str, TS[tuple[OrderResponse, ...]]])

        order_client_input = order_client.wire_impl_inputs_stub(path).request
        requests = _convert_to_tsd_by_order_id(order_client_input)

        _compute_order_state = _compute_order_state_single if order_state_tp is SingleLegOrder else _compute_order_state_multi
        order_state = map_(_compute_order_state, requests, order_responses_fb())
        order_states.wire_impl_out_stub(path, order_state)

        if needs_map:
            result: TSD[str, TS[tuple[OrderResponse, ...]]] = \
                map_(lambda request_, order_state_: _to_tuple(fn(unroll(request_), order_state_)), requests,
                     order_state)
        else:
            requests = _flatten(requests)
            result: TSD[str, TS[tuple[OrderResponse, ...]]] = \
                fn(requests, order_state)

        order_responses_fb(result)
        order_client_outputs = _map_response_to_request(order_client_input, result)
        order_client.wire_impl_out_stub(path, order_client_outputs)

    return _order_handler_impl


@dataclass
class MapRequestToIdSate:
    requests: dict[tuple: int] = field(default_factory=dict)


def _key_from_request(request: OrderRequest) -> tuple:
    return request.order_id, request.version, request.user_id


@compute_node(valid=("requests",))
def _map_response_to_request(
        requests: TSD[int, TS[OrderRequest]], responses: TSD[str, TS[tuple[OrderResponse, ...]]],
        _state: STATE[MapRequestToIdSate] = None) -> TSD[int, TS[OrderResponse]]:
    d = _state.requests
    if requests.modified:
        for key, request in requests.modified_items():
            d[_key_from_request(request.value)] = key
    if responses.modified:
        out = {}
        for responses_ in responses.modified_values():
            for response in responses_.value:
                request = response.original_request
                key = d.pop(_key_from_request(request))
                out[key] = response
        return out


@compute_node
def _to_tuple(ts: TS[OrderResponse]) -> TS[tuple[OrderResponse, ...]]:
    return (ts.value,)


@compute_node
def _flatten(tsd: TSD[str, TS[tuple[OrderRequest, ...]]]) -> TS[tuple[OrderRequest, ...]]:
    return tuple(r for requests in tsd.modified_values() for r in requests)


@compute_node
def _convert_to_tsd_by_order_id(requests: TSD[int, TS[OrderRequest]]) -> TSD[str, TS[tuple[OrderRequest, ...]]]:
    out = defaultdict(list)
    for request in requests.modified_values():
        request = request.value
        out[request.order_id].append(request)
    return frozendict({k: tuple(v) for k, v in out.items()})


@dataclass
class PendingRequests:
    pending_requests: list[OrderRequest] = field(default_factory=list)


@compute_node(valid=("requests",))
def _compute_order_state_single(
        requests: TS[tuple[OrderRequest, ...]],
        responses: TS[tuple[OrderResponse, ...]],
        _state: STATE[PendingRequests] = None,
        _output: TSB_OUT[OrderState[ORDER]] = None
) -> TSB[OrderState[SingleLegOrder]]:
    out_confirmed = {}
    out_requested = {}
    confirmed = _output.confirmed.value
    requested = _output.requested.value

    if responses.modified:
        responses = {response.version: response for response in responses.value}
        _state.pending_requests = [request for request in _state.pending_requests if request.version not in responses]
        # Apply responses to confirmed state
        for response in responses.values():
            confirmed, delta = apply_confirmation(confirmed, response)
            out_confirmed.update(delta)

        requested = confirmed
        out_requested = requested
        for request in _state.pending_requests:
            requested, delta = apply_requested_single_leg(requested, request)
            out_requested.update(delta)

    if requests.modified:
        _state.pending_requests.extend(requests.value)
        for request in requests.value:
            requested, delta = apply_requested_single_leg(requested, request)
            out_requested.update(delta)

    return {"requested": out_requested, "confirmed": out_confirmed}


def apply_confirmation(confirmed: dict, response: OrderResponse) -> tuple[Any, dict]:
    request = response.original_request
    if isinstance(request, CreateOrderRequest):
        order_type: SingleLegOrderType = request.order_type
        v = dict(
            order_id=request.order_id,
            order_version=request.version,
            last_updated_by=request.user_id,
            order_type=request.order_type,
            originator_info=request.originator_info,
            is_done=False,
            suspension_keys=frozenset(),
            is_suspended=False,
            remaining_qty=order_type.quantity,
            filled_qty=dict(qty=0.0, unit=order_type.quantity.unit),
            filled_notional=dict(price=0.0),
            is_filled=False,
        )
        return v, v


def apply_requested_single_leg(requested: dict, request: OrderRequest) -> tuple[Any, dict]:
    if isinstance(request, CreateOrderRequest):
        order_type: SingleLegOrderType = request.order_type
        v = dict(
            order_id=request.order_id,
            order_version=request.version,
            last_updated_by=request.user_id,
            order_type=request.order_type,
            originator_info=request.originator_info,
            is_done=False,
            suspension_keys=frozenset(),
            is_suspended=False,
            remaining_qty=order_type.quantity,
            filled_qty=dict(qty=0.0, unit=order_type.quantity.unit),
            filled_notional=dict(price=0.0),
            is_filled=False,
        )
        return v, v


@compute_node
def _compute_order_state_multi(
        requests: TS[tuple[OrderRequest, ...]],
        responses: TS[tuple[OrderResponse, ...]],
        _state: STATE[PendingRequests] = None,
        _output: TSB_OUT[OrderState[ORDER]] = None
) -> TSB[OrderState[MultiLegOrderType]]:
    ...
