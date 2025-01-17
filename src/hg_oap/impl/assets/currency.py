from enum import Enum

from hg_oap.assets.currency import Currency
from hg_oap.units import PrimaryUnit
from hg_oap.units.default_unit_system import U


class Currencies(Enum):
    """The collection of known currencies"""
    EUR = Currency(symbol="EUR", minor_currency_ratio=100)
    GBP = Currency(symbol="GBP", minor_currency_ratio=100)
    USD = Currency(symbol="USD", minor_currency_ratio=100)


U.us_dollars = U.money.us_dollars
U.USD = PrimaryUnit(dimension=U.us_dollars)
U.USX = 0.01 * U.USD

U.euros = U.money.euros
U.EUR = PrimaryUnit(dimension=U.euros)
U.EUX = 0.01 * U.EUR

U.pounds = U.money.pounds
U.GBP = PrimaryUnit(dimension=U.pounds)
U.GBX = 0.01 * U.GBP

