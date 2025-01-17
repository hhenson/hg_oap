from dataclasses import dataclass
from enum import Enum

from hg_oap.assets.asset import PhysicalAsset
from hg_oap.units.default_unit_system import U


@dataclass(frozen=True)
class Commodity(PhysicalAsset):
    """
    Metals, Food, etc.
    """


@dataclass(frozen=True)
class BaseMetal(Commodity):
    """
    Metals such as Copper.
    """


class BaseMetals(Enum):
    MAL = BaseMetal(symbol="MAL", name="Aluminium", default_unit=U.mt)
    MCU = BaseMetal(symbol="MCU", name="Copper", default_unit=U.mt)
    MNI = BaseMetal(symbol="MNI", name="Nickel", default_unit=U.mt)
    MPB = BaseMetal(symbol="MPB", name="Lead", default_unit=U.mt)
    MSN = BaseMetal(symbol="MSN", name="Tin", default_unit=U.mt)
    MZN = BaseMetal(symbol="MZN", name="Zinc", default_unit=U.mt)


@dataclass(frozen=True)
class PreciousMetal(Commodity):
    """
    Gold, Silver, Platinum, Palladium.
    """


class PreciousMetals(Enum):
    XAU = PreciousMetal(symbol="XAU", name="Gold", default_unit=U.toz)
    XAG = PreciousMetal(symbol="XAG", name="Silver", default_unit=U.toz)
    XPD = PreciousMetal(symbol="XPD", name="Palladium", default_unit=U.toz)
    XPT = PreciousMetal(symbol="XPT", name="Platinum", default_unit=U.toz)


@dataclass(frozen=True)
class Energy(Commodity):
    """
    Oil, Gas, etc.
    """

class EnergyAssets(Enum):
    WTI = Energy(symbol="WTI", name="Crude Oil WTI")
    Brent = Energy(symbol="Brent", name="Crude Oil Brent")
    NG = Energy(symbol="NG", name="Natural Gas")
    RBOB = Energy(symbol="RBOB", name="RBOB Gasoline")
    LSGO = Energy(symbol="LSGO", name="Low Sulphur Gas Oil")
    HO = Energy(symbol="HO", name="ULS Diesel")


@dataclass(frozen=True)
class LiveStock(Commodity):
    """
    Live Cattle, Lean Hogs.
    """


class LiveStockAssets(Enum):
   LC = LiveStock(symbol="LC", name="Live Cattle")
   HE = LiveStock(symbol="HE", name="Lean Hogs")


@dataclass(frozen=True)
class Softs(Commodity):
    """
    Cocoa, Coffee, Cotton, Sugar.
    """


class SoftsAssets(Enum):
    CC = Softs(symbol="CC", name="Cocoa")
    KC = Softs(symbol="KC", name="Coffee")
    CT = Softs(symbol="CT", name="Cotton")
    SB = Softs(symbol="SB", name="Sugar")


@dataclass(frozen=True)
class Grains(Commodity):
    """
    Corn, Wheat, Soybeans.
    """


class GrainsAssets(Enum):
    C = Grains(symbol="C", name="Corn")
    W = Grains(symbol="W", name="Wheat")
    S = Grains(symbol="S", name="Soybeans")
    SM = Grains(symbol="SM", name="Soybean Meal")
    BO = Grains(symbol="BO", name="Soybean Oil")


