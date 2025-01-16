from typing import Type

import polars as pl
from frozendict import frozendict

from hg_oap.pricing_service import TIMED_VALUE, TimedValue, TIMED_VALUE_1, TIMED_VALUE_BUNDLE
from hgraph import compute_node, add_, TS, Frame, mul_, NUMBER, div_, zero, WiringNodeClass, pow_, graph, convert, \
    const, TSD, sub_, AUTO_RESOLVE, TSB


@graph(overloads=zero)
def zero_timed_value(
    tp: Type[TS[TIMED_VALUE]], op: WiringNodeClass, tp_: type[TIMED_VALUE] = AUTO_RESOLVE
) -> TS[TIMED_VALUE]:
    mapping = {"mul_": tp_.mul_null, "add_": tp_.null, "zero": tp_.null}

    return const(mapping[op.signature.name], TS[tp_])


@compute_node(overloads=add_)
def add_timed_value(lhs: TS[TIMED_VALUE], rhs: TS[TIMED_VALUE]) -> TS[TIMED_VALUE]:
    return lhs.value + rhs.value


@compute_node(overloads=add_)
def add_timed_value_tsb(lhs: TSB[TIMED_VALUE_BUNDLE], rhs: TSB[TIMED_VALUE_BUNDLE]) -> TSB[TIMED_VALUE_BUNDLE]:
    return lhs.value + rhs.value


@compute_node(overloads=sub_)
def sub_timed_value(lhs: TS[TIMED_VALUE], rhs: TS[TIMED_VALUE]) -> TS[TIMED_VALUE]:
    return lhs.value - rhs.value


@compute_node(overloads=mul_)
def mul_timed_value(lhs: TS[TIMED_VALUE], rhs: TS[NUMBER]) -> TS[TIMED_VALUE]:
    return lhs.value * rhs.value


@compute_node(overloads=div_)
def div_timed_value(lhs: TS[TIMED_VALUE], rhs: TS[NUMBER]) -> TS[TIMED_VALUE]:
    return lhs.value / rhs.value


@graph(overloads=zero)
def zero_timed_value_frame(tp: Type[TS[Frame[TimedValue]]], op: WiringNodeClass) -> TS[Frame[TimedValue]]:
    mapping = {"add_": frozendict({})}
    return convert[TS[Frame[TimedValue]]](const(mapping[op.signature.name], TSD[str, TS[TimedValue]]))


@compute_node(overloads=add_)
def add_timed_value_frames(lhs: TS[Frame[TIMED_VALUE]], rhs: TS[Frame[TIMED_VALUE]]) -> TS[Frame[TIMED_VALUE]]:
    lhs_value = lhs.value
    rhs_value = rhs.value
    if lhs_value.is_empty():
        return rhs_value
    if rhs_value.is_empty():
        return lhs_value

    return lhs_value.join(rhs_value, on="timestamp", how="inner", suffix="_right").select(
        timestamp=pl.col("timestamp"), val=pl.col("val") + pl.col("val_right")
    )


@compute_node(overloads=mul_)
def mul_timed_value_frames(lhs: TS[Frame[TIMED_VALUE]], rhs: TS[Frame[TIMED_VALUE_1]]) -> TS[Frame[TIMED_VALUE]]:
    lhs_value = lhs.value
    rhs_value = rhs.value
    if lhs_value is TimedValue.null_frame:
        return rhs_value
    if rhs_value is TimedValue.null_frame:
        return lhs_value

    return lhs_value.join(rhs_value, on="timestamp", how="inner", suffix="_right").select(
        timestamp=pl.col("timestamp"), val=pl.col("val") * pl.col("val_right")
    )


@compute_node(overloads=mul_)
def mul_timed_value_frame(lhs: TS[Frame[TIMED_VALUE]], rhs: TS[NUMBER]) -> TS[Frame[TIMED_VALUE]]:
    lhs = lhs.value
    if not lhs.is_empty():
        return lhs.with_columns(val=pl.col("val") * rhs.value)


@compute_node(overloads=div_)
def div_timed_value_frame(lhs: TS[Frame[TIMED_VALUE]], rhs: TS[NUMBER]) -> TS[Frame[TIMED_VALUE]]:
    lhs = lhs.value
    if not lhs.is_empty():
        return lhs.with_columns(val=pl.col("val") / rhs.value)


@compute_node(overloads=pow_)
def pow_timed_value_frame(lhs: TS[Frame[TIMED_VALUE]], rhs: TS[NUMBER]) -> TS[Frame[TIMED_VALUE]]:
    lhs = lhs.value
    if not lhs.is_empty():
        return lhs.with_columns(val=pl.col("val") ** rhs.value)
