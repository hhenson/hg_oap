from dataclasses import dataclass
from numbers import Number

from hg_oap.units.unit import Unit
from hgraph import CompoundScalar, compute_node, div_, TS, mul_, add_, sub_, DivideByZero

__all__ = ("Quantity",)


EPSILON = 1e-9


@dataclass(frozen=True, eq=False, unsafe_hash=True, repr=False)
class Quantity(CompoundScalar):
    qty: float
    unit: Unit

    def __str__(self):
        return f"{self.qty} {self.unit}"

    def __repr__(self):
        return f"{self.qty}*{self.unit}"

    def __eq__(self, other):
        if isinstance(other, Quantity):
            other_qty = other.unit.convert(other.qty, to=self.unit)
            return other_qty - EPSILON <= self.qty <= other_qty + EPSILON
        else:
            return NotImplemented

    def __add__(self, other):
        if isinstance(other, Quantity):
            ret, conv = self.unit + other.unit
            return Quantity(self.qty + other.unit.convert(other.qty, to=conv), ret)
        else:
            return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Quantity):
            ret, conv = self.unit - other.unit
            return Quantity(self.qty - other.unit.convert(other.qty, to=conv), ret)
        else:
            return NotImplemented

    def __mul__(self, other):
        if isinstance(other, Number):
            return Quantity(self.qty * other, self.unit)
        elif isinstance(other, Quantity):
            return Quantity(self.qty * other.qty, self.unit * other.unit)
        else:
            return NotImplemented

    __rmul__ = __mul__

    def __truediv__(self, other):
        if isinstance(other, Number):
            return Quantity(self.qty / other, self.unit)
        elif isinstance(other, Quantity):
            return Quantity(self.qty / other.qty, self.unit / other.unit)
        else:
            return NotImplemented

    def __rtruediv__(self, other):
        return Quantity(float(other) / self.qty, self.unit ** -1)

    def __pow__(self, other):
        if isinstance(other, Number):
            return Quantity(self.qty ** other, self.unit**other)
        else:
            return NotImplemented

    def __round__(self, n=None):
        return Quantity(round(self.qty, n), self.unit)

    def __lt__(self, other):
        if isinstance(other, Quantity):
            return self.qty < other.unit.convert(other.qty, to=self.unit)
        else:
            return NotImplemented

    def __le__(self, other):
        if isinstance(other, Quantity):
            return self.qty <= other.unit.convert(other.qty, to=self.unit)
        else:
            return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Quantity):
            return self.qty > other.unit.convert(other.qty, to=self.unit)
        else:
            return NotImplemented

    def __ge__(self, other):
        if isinstance(other, Quantity):
            return self.qty >= other.unit.convert(other.qty, to=self.unit)
        else:
            return NotImplemented

    def __abs__(self):
        return Quantity(abs(self.qty), self.unit)

    def __neg__(self):
        return Quantity(-self.qty, self.unit)

    def __pos__(self):
        return Quantity(+self.qty, self.unit)

    def as_(self, unit):
        return Quantity(self.unit.convert(self.qty, to=unit), unit)


@compute_node(overloads=div_)
def div_qty(lhs: TS[Quantity], rhs: TS[Quantity], divide_by_zero: DivideByZero = DivideByZero.ERROR) -> TS[Quantity]:
    try:
        return lhs.value / rhs.value
    except ZeroDivisionError:
        if divide_by_zero is DivideByZero.NAN:
            return Quantity(qty=float("NaN"), unit=lhs.value.unit/rhs.value.unit)
        elif divide_by_zero is DivideByZero.INF:
            return Quantity(qty=float("inf"), unit=lhs.value.unit/rhs.value.unit)
        elif divide_by_zero is DivideByZero.NONE:
            return
        else:
            raise


@compute_node(overloads=div_)
def div_qty_float(lhs: TS[Quantity], rhs: TS[float], divide_by_zero: DivideByZero = DivideByZero.ERROR) -> TS[Quantity]:
    try:
        return lhs.value / rhs.value
    except ZeroDivisionError:
        if divide_by_zero is DivideByZero.NAN:
            return Quantity(qty=float("NaN"), unit=lhs.value.unit)
        elif divide_by_zero is DivideByZero.INF:
            return Quantity(qty=float("inf"), unit=lhs.value.unit)
        elif divide_by_zero is DivideByZero.NONE:
            return
        else:
            raise


@compute_node(overloads=mul_)
def mul_qty(lhs: TS[Quantity], rhs: TS[Quantity]) -> TS[Quantity]:
    return lhs.value * rhs.value


@compute_node(overloads=mul_)
def mul_qty_float(lhs: TS[Quantity], rhs: TS[float]) -> TS[Quantity]:
    return lhs.value * rhs.value


@compute_node(overloads=add_)
def add_qty(lhs: TS[Quantity], rhs: TS[Quantity]) -> TS[Quantity]:
    return lhs.value + rhs.value


@compute_node(overloads=sub_)
def sub_qty(lhs: TS[Quantity], rhs: TS[Quantity]) -> TS[Quantity]:
    return lhs.value - rhs.value
