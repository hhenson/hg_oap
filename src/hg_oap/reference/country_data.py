from dataclasses import dataclass
from enum import Enum

from hgraph import CompoundScalar

from hg_oap.assets.currency import Currency, Currencies


@dataclass
class Country(CompoundScalar):
    iso2: str
    iso3: str
    name: str
    currency: Currency


@dataclass
class EconomicRegion(CompoundScalar):
    name: str
    countries: frozenset[Country]


class Countries(Enum):
    CA = Country("CA", "CAN", "Canada", Currencies.CAD.value)
    DE = Country("DE", "DEU", "Germany", Currencies.EUR.value)
    FR = Country("FR", "FRA", "France", Currencies.EUR.value)
    GB = Country("GB", "GBR", "United Kingdom", Currencies.GBP.value)
    US = Country("US", "USA", "United States", Currencies.USD.value)
    ZA = Country("ZA", "ZAF", "South Africa", Currencies.ZAR.value)


class EconomicRegions(Enum):
    NA = EconomicRegion("NA", frozenset({Countries.CA.value, Countries.US.value}))
    EU = EconomicRegion("EU", frozenset({Countries.FR.value, Countries.DE.value}))
