from datetime import datetime
from typing import Type

from hg_oap.pricing_service import Price, PRICE, PriceType
from hg_oap.units import Unit
from hgraph import (mul_, TSB, TS, NUMBER, compute_node, add_, graph, sub_, div_, combine, TIME_SERIES_TYPE, sink_node,
                    WiringNodeClass, zero, MIN_DT, SCALAR, AUTO_RESOLVE, DivideByZero)
from hgraph.stream.stream import Stream, combine_statuses, combine_status_messages, merge_join, StreamStatus

__all__ = ("add_price_stream_number", "sub_price_stream_number", "mul_price_stream_number", "div_price_stream_number",
           "add_two_price_streams", "sub_two_price_streams", "mul_two_price_streams", "div_two_price_streams",
           "zero_price", "combine_origins", "combine_two_price_streams",
           "assert_not_equal", "combine_price_types", "combine_timestamps")


@graph(overloads=add_)
def add_price_stream_number(lhs: TSB[Stream[Price]], rhs: TS[NUMBER]) -> TSB[Stream[Price]]:
    return lhs.copy_with(val=lhs.val + rhs)


@graph(overloads=sub_)
def sub_price_stream_number(lhs: TSB[Stream[Price]], rhs: TS[NUMBER]) -> TSB[Stream[Price]]:
    return lhs.copy_with(val=lhs.val - rhs)


@graph(overloads=mul_)
def mul_price_stream_number(lhs: TSB[Stream[Price]], rhs: TS[NUMBER]) -> TSB[Stream[Price]]:
    return lhs.copy_with(val=lhs.val * rhs)


@graph(overloads=div_)
def div_price_stream_number(lhs: TSB[Stream[Price]], rhs: TS[NUMBER],
                            divide_by_zero: DivideByZero = DivideByZero.NAN) -> TSB[Stream[Price]]:
    return lhs.copy_with(val=div_(lhs.val, rhs, divide_by_zero))


@graph(overloads=add_)
def add_two_price_streams(lhs: TSB[Stream[Price]], rhs: TSB[Stream[Price]]) -> TSB[Stream[Price]]:
    return combine_two_price_streams(lhs, rhs, lhs.val + rhs.val)


@graph(overloads=sub_)
def sub_two_price_streams(lhs: TSB[Stream[Price]], rhs: TSB[Stream[Price]]) -> TSB[Stream[Price]]:
    return combine_two_price_streams(lhs, rhs, lhs.val - rhs.val)


@graph(overloads=mul_)
def mul_two_price_streams(lhs: TSB[Stream[Price]], rhs: TSB[Stream[Price]]) -> TSB[Stream[Price]]:
    return combine_two_price_streams(lhs, rhs, lhs.val * rhs.val)


@graph(overloads=div_)
def div_two_price_streams(lhs: TSB[Stream[Price]],
                          rhs: TSB[Stream[Price]],
                          divide_by_zero: DivideByZero = DivideByZero.NAN) -> TSB[Stream[Price]]:
    return combine_two_price_streams(lhs, rhs, div_(lhs.val, rhs.val, divide_by_zero))


@graph
def combine_two_price_streams(lhs: PRICE,
                              rhs: PRICE,
                              price: TS[SCALAR],
                              price_type: Type[PRICE] = AUTO_RESOLVE,
                              __strict__: bool = True) -> PRICE:
    if __strict__:
        assert_equal(lhs.currency_unit, rhs.currency_unit,
                     "Cannot combine two price streams with different currency units: {} / {}")
        assert_equal(lhs.unit, rhs.unit,
                     "Cannot combine two price streams with different units: {} / {}")

    return combine[price_type](
        currency_unit=combine_units(lhs.currency_unit, rhs.currency_unit),
        origin=combine_origins(lhs.origin, rhs.origin),
        price_type=combine_price_types(lhs.price_type, rhs.price_type),
        val=price,
        unit=combine_units(lhs.unit, rhs.unit),
        status=combine_statuses(lhs.status, rhs.status),
        status_msg=combine_status_messages(lhs.status_msg, rhs.status_msg),
        timestamp=combine_timestamps(lhs.timestamp, rhs.timestamp))


@compute_node(valid=())
def combine_units(lhs: TS[Unit], rhs: TS[Unit]) -> TS[Unit]:
    return lhs.value if lhs.valid else rhs.value


@sink_node
def assert_equal(ts1: TIME_SERIES_TYPE, ts2: TIME_SERIES_TYPE, error_template: str):
    if ts1.value != ts2.value:
        raise AssertionError(error_template.format(ts1.value, ts2.value))


@sink_node
def assert_not_equal(ts1: TIME_SERIES_TYPE, ts2: TIME_SERIES_TYPE, error_template: str):
    if ts1.value == ts2.value:
        raise AssertionError(error_template.format(ts1.value, ts2.value))


@graph
def combine_origins(origin1: TS[str], origin2: TS[str]) -> TS[str]:
    return merge_join(origin1, origin2, separator="/")


@compute_node(valid=())
def combine_timestamps(lhs: TS[datetime], rhs: TS[datetime]) -> TS[datetime]:
    if not lhs.valid:
        return rhs.value
    elif not rhs.valid:
        return lhs.value
    else:
        return max(lhs.value.replace(tzinfo=None), rhs.value.replace(tzinfo=None))


@compute_node(valid=())
def combine_price_types(lhs: TS[PriceType], rhs: TS[PriceType]) -> TS[PriceType]:
    lhs = lhs.value
    rhs = rhs.value
    if lhs in (None, PriceType.NONE):
        return rhs
    elif rhs in (None, PriceType.NONE):
        return lhs
    elif lhs is rhs:
        return lhs
    else:
        match lhs:
            case PriceType.MODEL:
                return PriceType.MODEL
            case PriceType.FIXED:
                return rhs
            case _:
                match rhs:
                    case PriceType.MODEL: return PriceType.MODEL
                    case PriceType.FIXED: return lhs
                    case _: return PriceType.IMPLIED


@graph(overloads=zero)
def zero_price(tp: Type[TSB[Stream[Price]]], op: WiringNodeClass) -> TSB[Stream[Price]]:
    return combine[tp](status=StreamStatus.OK,
                      status_msg="",
                      val=0.0,
                      timestamp=MIN_DT,
                      origin="")
