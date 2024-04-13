from dataclasses import dataclass

from hgraph import TimeSeriesSchema, TS, TSS

from hg_oap.orders.order_type import OrderType
from hg_oap.quanity.price_unit import Price
from hg_oap.quanity.quantity import Quantity
from hg_oap.quanity.unit import CompoundUnit


@dataclass
class OriginatorInfo(CompoundUnit):
    account: str


@dataclass
class Order(TimeSeriesSchema):
    order_id: TS[str]
    order_type: TS[OrderType]
    originator_info: TS[OriginatorInfo]
    remaining_qty: TS[Quantity]
    filled_qty: TS[Quantity]
    filled_notional: TS[Price]
    is_filled: TS[bool]
    suspension_keys: TSS[str]
    is_suspended: TS[bool]
