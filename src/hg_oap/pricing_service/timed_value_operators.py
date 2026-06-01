from typing import Type

import polars as pl
from frozendict import frozendict

from hg_oap.pricing_service import TIMED_VALUE, TIMED_VALUE_1, TIMED_VALUE_BUNDLE, TimedValue
from hg_oap.utils import replace
from hgraph import (
    AUTO_RESOLVE,
    NUMBER,
    TS,
    TSB,
    TSD,
    Frame,
    WiringNodeClass,
    abs_,
    add_,
    compute_node,
    const,
    convert,
    div_,
    graph,
    mean,
    mul_,
    pow_,
    std,
    sub_,
    zero,
    DivideByZero,
)


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
def div_timed_value(
    lhs: TS[TIMED_VALUE], rhs: TS[NUMBER],
    divide_by_zero: DivideByZero = DivideByZero.ERROR) -> TS[TIMED_VALUE]:
    try:
        return lhs.value / rhs.value
    except ZeroDivisionError:
        if divide_by_zero is DivideByZero.NAN:
            return replace(lhs, val=float("NaN"))
        elif divide_by_zero is DivideByZero.INF:
            return replace(lhs, val=float("inf"))
        elif divide_by_zero is DivideByZero.NONE:
            return
        else:
            raise


@graph(overloads=zero)
def zero_timed_value_frame(tp: Type[TS[Frame[TimedValue]]], op: WiringNodeClass) -> TS[Frame[TimedValue]]:
    mapping = {"add_": frozendict(), "zero": frozendict()}
    return convert[TS[Frame[TimedValue]]](const(mapping[op.signature.name], TSD[str, TS[TimedValue]]))


@compute_node(overloads=add_)
def add_timed_value_frames(
    lhs: TS[Frame[TIMED_VALUE]],
    rhs: TS[Frame[TIMED_VALUE]],
    __strict__: bool = True
) -> TS[Frame[TIMED_VALUE]]:
    lhs_value = lhs.value
    rhs_value = rhs.value
    if lhs_value.is_empty():
        return rhs_value
    if rhs_value.is_empty():
        return lhs_value

    if __strict__:
        return lhs_value.join(rhs_value, on="timestamp", how="inner", suffix="_right").select(
            timestamp=pl.col("timestamp"), val=pl.col("val").fill_null(0.) + pl.col("val_right").fill_null(0.)
        ).sort("timestamp")
    else:
        return lhs_value.join(rhs_value, on="timestamp", how="full", suffix="_right", coalesce=True).select(
            timestamp=pl.col("timestamp"), val=pl.col("val").fill_null(0.) + pl.col("val_right").fill_null(0.)
        ).sort("timestamp")


@compute_node(overloads=sub_)
def sub_timed_value_frames(
    lhs: TS[Frame[TIMED_VALUE]],
    rhs: TS[Frame[TIMED_VALUE]],
    __strict__: bool = True
) -> TS[Frame[TIMED_VALUE]]:
    lhs_value = lhs.value
    rhs_value = rhs.value
    if lhs_value.is_empty():
        return rhs_value.select("timestamp", val=-pl.col("val"))
    if rhs_value.is_empty():
        return lhs_value

    if __strict__:
        return lhs_value.join(rhs_value, on="timestamp", how="inner", suffix="_right").select(
            timestamp=pl.col("timestamp"), val=pl.col("val").fill_null(0.) - pl.col("val_right").fill_null(0.)
        ).sort("timestamp")
    else:
        return lhs_value.join(rhs_value, on="timestamp", how="full", suffix="_right", coalesce=True).select(
            timestamp=pl.col("timestamp"), val=pl.col("val").fill_null(0.) - pl.col("val_right").fill_null(0.)
        ).sort("timestamp")


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
def div_timed_value_frame(
    lhs: TS[Frame[TIMED_VALUE]],
    rhs: TS[NUMBER],
    divide_by_zero: DivideByZero = DivideByZero.ERROR
) -> TS[Frame[TIMED_VALUE]]:
    # Ignore divide_by_zero - polars does its own thing
    lhs = lhs.value
    if not lhs.is_empty():
        return lhs.with_columns(val=pl.col("val") / rhs.value)


@compute_node(overloads=pow_)
def pow_timed_value_frame(
    lhs: TS[Frame[TIMED_VALUE]],
    rhs: TS[NUMBER],
    divide_by_zero: DivideByZero = DivideByZero.ERROR
) -> TS[Frame[TIMED_VALUE]]:
    # Ignore divide_by_zero - polars does its own thing
    lhs = lhs.value
    if not lhs.is_empty():
        return lhs.with_columns(val=pl.col("val") ** rhs.value)


@compute_node(overloads=abs_)
def abs_timed_value_frame(lhs: TS[Frame[TIMED_VALUE]]) -> TS[Frame[TIMED_VALUE]]:
    lhs = lhs.value
    if lhs.is_empty():
        return lhs
    else:
        return lhs.with_columns(val=pl.col("val").abs())


@compute_node(overloads=std)
def std_timed_value_frame(df: TS[Frame[TIMED_VALUE]]) -> TS[float]:
    df = df.value
    if len(df) <= 1:
        return 0.0
    else:
        return df['val'].std()


@compute_node(overloads=mean)
def mean_timed_value_frame(df: TS[Frame[TIMED_VALUE]]) -> TS[float]:
    df = df.value
    if len(df) == 0:
        return float('NaN')
    else:
        return df['val'].mean()
