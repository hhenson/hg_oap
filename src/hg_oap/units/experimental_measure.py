from dataclasses import dataclass, field
from decimal import Decimal
from typing import NamedTuple, TypeVar, Generic

from hg_oap.utils.exprclass import ExprClass


@dataclass(frozen=True)
class Unit(ExprClass):
    symbol: str
    name: str


@dataclass(frozen=True)
class DerivedUnit(Unit):
    parent: Unit
    ratio: Decimal


@dataclass
class Category:
    name: str
    is_a: set["Category"] = field(default_factory=lambda: set())
    has_a: set["Category"] = field(default_factory=lambda: set())
    units: set[Unit] = field(default_factory=lambda: set())


UNIT = TypeVar("UNIT", bound=Unit)
UNIT_1 = TypeVar("UNIT_1", bound=Unit)

CATEGORY = TypeVar("CATEGORY", bound=Category)
CATEGORY_1 = TypeVar("CATEGORY_1", bound=Category)


@dataclass(frozen=True, slots=True)
class UnitCategory(Generic[UNIT, CATEGORY]):
    unit: UNIT
    category: CATEGORY


@dataclass(frozen=True, slots=True)
class Measure(UnitCategory[UNIT, CATEGORY], Generic[UNIT, CATEGORY]):
    qty: float


def create_unit_category(unit: Unit, category: Category) -> UnitCategory:
    # Validated that the unit / category pair is valid.
    return UnitCategory(unit=unit, category=category)


def create_measure(qty: float, unit: UNIT = None, category: CATEGORY = None,
                   unit_category: UnitCategory[UNIT, CATEGORY] = None) -> Measure:
    if unit_category is None:
        assert unit is not None
        assert category is not None
        unit_category = create_unit_category(unit, category)
    return Measure(qty=qty, unit=unit_category.unit, category=unit_category.category)


def convert_to_unit(measure: Measure[UNIT, CATEGORY], unit: UNIT_1) -> Measure:
    """Converts the units of a measure to another set of units"""
    # Validate that the unit meaningful in the context of this category
    unit_category = create_unit_category(unit, measure.category)
    if is_a(measure.unit, unit):  # is this unit related
        return create_measure(measure.qty * ratio_of(measure.unit, unit),
                              unit_category=unit_category)
    else is_convertable(measure.unit, unit):
        new_qty = _convert(measure.category, measure.unit, unit, measure.qty)
        return create_measure(new_qty, unit_category=unit_category)

def convert_to_category(measure: Measure[UNIT, CATEGORY],
                        category: CATEGORY_1, unit: UNIT_1 = None) -> Category[UNIT_1, CATEGORY]:
    """Converts the measure to a specific unit and category"""
    # If the unit is None then assume we are only converting from the measure's units
    # in the measure's category to units in the new categories equivalent.

def add_(lhs: Measure[UNIT, CATEGORY], rhs: Measure[UNIT_1, CATEGORY]) -> Measure[UNIT, CATEGORY]:
    ...


def sub_(lhs: Measure[UNIT, CATEGORY], rhs: Measure[UNIT_1, CATEGORY]) -> Measure[UNIT, CATEGORY]:
    ...


def mul_(lhs: Measure[UNIT, CATEGORY], rhs: Measure[UNIT, CATEGORY] | float) -> Measure[UNIT, CATEGORY]:
    ...


def div_(lhs: Measure[UNIT, CATEGORY], rhs: Measure[UNIT, CATEGORY] | float) -> Measure[UNIT, CATEGORY]:
    ...


lot = Unit(symbol='L', name='lot')
usd = Unit(symbol='USD', name='US Dollar')

ounce = Unit(symbol='oz', name="ounce")
gram = Unit(symbol='g', name="gram")
kilogram = DerivedUnit(symbol='kg', name='kilogram', parent=gram, ratio=Decimal("1000.0"))
milligram = DerivedUnit(symbol='mg', name='milligram', parent=gram, ratio=Decimal("0.001"))
microgram = DerivedUnit(symbol='ug', name='microgram', parent=gram, ratio=Decimal("0.000001"))

weight = Category(name='weight')
imperial_weights = Category(name='imperial weight', is_a={weight}, units={ounce})
si_weights = Category(name='si weight', is_a={weight}, units={gram, kilogram, milligram, microgram})

currency = Category(name='currency', )
currency_usd = Category(name='usd', is_a={currency}, units={usd})

asset = Category(name='asset')
metal = Category(name='metal', is_a={asset})

contract = Category(name='contract', units={lot})  # Has a definition of a lot

exchange = Category(name='exchange')
cme = Category(name='cme', is_a={exchange})

purity = Category(name='purity')
purity_975 = Category(name='97.5%', is_a={purity})

precious_metal = Category(name='precious_metal', is_a={metal}, has_a={purity})
gold = Category(name='gold', is_a={precious_metal})

cme_gold = Category(name='GC', is_a={gold}, has_a={purity_975, cme, currency, weight, contract})

trade_measure_amount = Measure(100.0, ounce, cme_gold)
trade_measure_price = Measure(1536.10, usd / ounce, cme_gold)

notion_cme_gold = trade_measure_amount * trade_measure_price

trade_lots = convert_to_unit(trade_measure_amount, lot)

"""
RULES
-----

A measure is a triple of qty, unit and category.



A measure can be operated on as follows:

Addition / Subtraction - There are two scenarios:

In all cases, the category must be the same, it is possible to convert to a common 
unit and category before performing any operator.

1. a + b  or a - b results in a unit of measure that is remains within the  same unit. 
   An example is length, one length - another length results in a length. In this case
   it is only possible to operate in the same unit. When two units are convertable, 
   the measure should be first converted to a single unit before applying the value.
   
2. a + b does not exist and a - b results in an alternative unit. For example datetime,
   there is no meaningful way to add two datetime values, but a - b results in timedelta.
   An alternative unit that represents a relative measure. This measure supports
   both add and subtract operations. Also a: datetime + b: timedelta -> datetime.
   
   In this case, the addition operator must operate on the same base unit.
   
Multiplication / Division:

In all cases the category must be the same. It is possible to convert to a common
category before performing any operator.

a * b or a / b results in a measure ( q1 * q2, u1 * u2, c ) or ( q1 / q2, u1 / u2, c)
The only constraint is that the units involved must be part of the category units,
either directly or via an is_a or has_a relationship. But this should be defined via 
construction, i.e. it is not possible to create a measure that is not valid.

"""
