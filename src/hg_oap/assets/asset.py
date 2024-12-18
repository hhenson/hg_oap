from dataclasses import dataclass

from hg_oap.units import Quantity
from hg_oap.units.default_unit_system import U
from hg_oap.units.unit import Unit
from hg_oap.units.unit_system import UnitConversionContext
from hg_oap.utils.exprclass import ExprClass
from hgraph import CompoundScalar


@dataclass(frozen=True)
class Asset(CompoundScalar, ExprClass, UnitConversionContext):
    """
    A thing of value that can be held.
    Assets are not instruments (i.e. cannot be traded directly), but can be used in instruments as underlyers.
    """
    symbol: str


@dataclass(frozen=True)
class PhysicalAsset(Asset):
    """
    A tangible thing, for example: raw materials, infrastructure, equipment, etc.

    The physical asset has a default unit - for example, copper is often measured in metric tonnes.
    TODO - is the default unit the size or price unit? e.g. MWh is price unit vs MW is contract size unit
        Does it make any sense to have it here?
    The actual traded unit can vary according to the contract - copper can be traded in pounds as well as tonnes.
    The unit conversion factors can be used to convert between units of different dimensions -
    e.g. density for mass/volume
    """
    name: str
    default_unit: Unit = U.NONE
    unit_conversion_factors: tuple[Quantity, ...] = ()


@dataclass(frozen=True)
class FinancialAsset(Asset):
    """
    A financial asset is a non-tangible asset. Examples include cash, cash equivalents, stocks and bonds.
    """
