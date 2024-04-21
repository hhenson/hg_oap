from dataclasses import dataclass, field
from typing import NamedTuple

from hg_oap.utils.exprclass import ExprClass


@dataclass(frozen=True)
class Unit(ExprClass):
    symbol: str
    name: str


@dataclass
class Category:
    name: str
    is_a: set["Category"] = field(default_factory=lambda: set())
    has_a: set["Category"] = field(default_factory=lambda: set())
    units: set[Unit] = field(default_factory=lambda: set())


Quantity = NamedTuple('Quantity', [('qty', float), ('unit', Unit)])
Measure = NamedTuple('Measure', [('qty', float), ('unit', Unit), ('category', Category)])


def convert_to_unit(measure: Measure, unit: Unit) -> Measure:
    """Converts the units of a measure to another set of units"""


def convert_to_category(measure: Measure, unit: Unit, category: Category) -> Category:
    """Converts the measure to a specific unit and category"""


def add_(lhs: Measure, rhs: Measure) -> Measure:
    ...

def sub_(lhs: Measure, rhs: Measure) -> Measure:
    ...

def mul_(lhs: Measure, rhs: Measure | float) -> Measure:
    ...


def div_(lhs: Measure, rhs: Measure | float) -> Measure:
    ...



lot = Unit(symbol='L', name='lot')
unit = Unit(symbol='', name='unit')
ounce = Unit(symbol='oz', name="ounce")
gram = Unit(symbol='g', name="gram")

weight = Category(name='weight')
imperial_weights = Category(name='imperial weight', is_a={weight}, units={ounce})
si_weights = Category(name='si weight', is_a={weight}, units={gram})

currency = Category(name='currency')
USD = Category(name='USD', is_a={currency})

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
trade_measure_price = Measure(1536.10, USD/ounce, cme_gold)

notion_cme_gold = trade_measure_amount * trade_measure_price

trade_lots = convert_to_unit(trade_measure_amount, lot)
