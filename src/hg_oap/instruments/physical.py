from dataclasses import dataclass

from hg_oap.impl.assets.commodities import Commodity
from hg_oap.instruments.instrument import Instrument
from hg_oap.units import Quantity


@dataclass(frozen=True)
class PhysicalCommodity(Instrument):
    asset: Commodity

    unit_conversion_factors: tuple[Quantity, ...] = lambda self: self.asset.unit_conversion_factors


