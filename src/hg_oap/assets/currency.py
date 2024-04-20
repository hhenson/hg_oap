from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from hg_oap.assets.asset import FinancialAsset
from hg_oap.units.dimension import PrimaryDimension
from hg_oap.units.unit import PrimaryUnit, DerivedUnit
from hg_oap.units.unit_system import UnitSystem


@dataclass(frozen=True)
class Currency(FinancialAsset):
    """
    The medium of exchange for goods and services, you may have used this. For example USD, EUR, GBP, etc.
    These represent the most commonly used currencies in the USA, Europe or the United Kingdom.
    """
    is_minor_currency: bool = False  # For example US cents rather than dollars

    def __post_init__(self):
        # Register currency units
        dimension = PrimaryDimension(name=f"{self.symbol}_Currency")
        PrimaryUnit(name=self.symbol, dimension=dimension)


@dataclass(frozen=True)
class MinorCurrency(Currency):
    """
    A minor currency is the fractional unit, for example US cents, typically this is a 1:100 ratio, the ratio
    is stored as ratio.
    """
    major_currency: Currency = None
    ratio: Decimal = Decimal("0.01")

    def __post_init__(self):
        DerivedUnit(primary_unit=getattr(UnitSystem.instance(), self.major_currency.symbol),
                    ratio=self.ratio,
                    name=self.symbol)

    def to_major_currency(self, value: float) -> float:
        return value * float(self.ratio)


class Currencies(Enum):
    """The collection of known currencies"""
    CAD = Currency(symbol="CAD")
    EUR = Currency(symbol="EUR")
    GBP = (gbp_ := Currency(symbol="GBP"))
    GBX = MinorCurrency(symbol="GBX", major_currency=gbp_)
    USD = (usd_ := Currency(symbol="USD"))
    USX = MinorCurrency(symbol="USX", major_currency=usd_)
    ZAR = Currency(symbol="ZAR")
