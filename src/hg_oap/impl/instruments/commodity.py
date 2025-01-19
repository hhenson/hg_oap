from enum import Enum

from hg_oap.impl.assets.commodities import BaseMetals
from hg_oap.dates.tenor import Tenor
from hg_oap.instruments.future import Future
from hg_oap.instruments.physical import PhysicalCommodity


class ThreeMonthBaseMetals(Enum):
    MAL_3M = Future("MAL_3M", Tenor("3m"), underlyer=BaseMetals.MAL)
    MCU_3M = Future("MCU_3M", Tenor("3m"), asset=BaseMetals.MCU)
    MNI_3M = Future("MNI_3M", Tenor("3m"), asset=BaseMetals.MNI)
    MPB_3M = Future("MPB_3M", Tenor("3m"), asset=BaseMetals.MPB)
    MSN_3M = Future("MSN_3M", Tenor("3m"), asset=BaseMetals.MSN)
    MZN_3M = Future("MZN_3M", Tenor("3m"), asset=BaseMetals.MZN)


class PhysicalCommodities(Enum):
    AH = PhysicalCommodity("AH", asset=BaseMetals.MAL)
    CA = PhysicalCommodity("CA", asset=BaseMetals.MCU)
    PB = PhysicalCommodity("PB", asset=BaseMetals.MPB)
    NI = PhysicalCommodity("NI", asset=BaseMetals.MNI)
    ZN = PhysicalCommodity("ZN", asset=BaseMetals.MZN)
    SN = PhysicalCommodity("SN", asset=BaseMetals.MSN)
