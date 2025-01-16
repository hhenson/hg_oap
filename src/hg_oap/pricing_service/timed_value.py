from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar, TypeVar

import polars as pl

from hgraph import CompoundScalar, NUMBER, clone_type_var, TimeSeriesSchema, MIN_DT

__all__ = ("TimedValue", "TIMED_VALUE", "TIMED_VALUE_1", "TIMED_VALUE_BUNDLE")


@dataclass(frozen=True)
class TimedValue(CompoundScalar):
    val: float
    timestamp: datetime

    null: ClassVar["TimedValue"]

    def __new__(cls, *args, **kwargs):
        if not len(args) and not len(kwargs):
            return cls.null

        return super().__new__(cls)

    def __neg__(self) -> "TimedValue":
        return type(self)(-self.val, self.timestamp)

    def __add__(self, other: "TimedValue") -> "TimedValue":
        if self is type(self).null:
            return other
        if other is type(other).null:
            return self

        return type(self)(self.val + other.val, max([self.timestamp, other.timestamp]))

    def __sub__(self, other: "TimedValue") -> "TimedValue":
        if self is type(self).null:
            return -other
        if other is TimedValue.null:
            return self

        return type(self)(self.val - other.val, max([self.timestamp, other.timestamp]))

    def __mul__(self, other: NUMBER) -> "TimedValue":
        return type(self)(self.val * other, self.timestamp)

    def __truediv__(self, other: NUMBER) -> "TimedValue":
        return type(self)(self.val / other, self.timestamp)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.null = cls(0.0, MIN_DT)
        cls.mul_null = cls(1.0, MIN_DT)


TimedValue.null = TimedValue(0.0, MIN_DT)
TimedValue.mul_null = TimedValue(1.0, MIN_DT)
TimedValue.null_frame = pl.DataFrame({})


TIMED_VALUE = TypeVar("TIMED_VALUE", bound=TimedValue)
TIMED_VALUE_1 = clone_type_var(TIMED_VALUE, "TIMED_VALUE_1")
TIMED_VALUE_BUNDLE = TypeVar("TIMED_VALUE_BUNDLE", bound=TimeSeriesSchema.from_scalar_schema(TimedValue))
