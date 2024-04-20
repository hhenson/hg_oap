from dataclasses import dataclass
from typing import ForwardRef

from hgraph import CompoundScalar

from hg_oap.assets.currency import Currency
from hg_oap.units.unit import Unit
from hg_oap.units.unit_system import UnitConversionContext


@dataclass(frozen=True)
class ContractClassification(CompoundScalar):
    """
    Describes a categorization of contracts to provide an ontology of contracts.
    """
    # TODO: Ensure that the parent is a superset of supported units
    name: str
    parent: ForwardRef("ContractClassification") | None  # TODO: How to support this in the AbstractSchema
    supported_qty_units: tuple[Unit, ...]
    supported_currencies: tuple[Currency, ...]
    qty_conversion_context: UnitConversionContext  # The conversion between qty unit dimensions


@dataclass(frozen=True)
class Contract(CompoundScalar):
    """
    Represents the term sheet of an instrument. Contracts represent details such as
    units that the instrument can be represented in, the default currency and alternative currencies
    that the instrument can be traded in etc.

    Contracts are able to be defined as recursive constructs, thus a base contract can be defined,
    with modifications made for specific instruments.
    """
    contract_specification: ContractClassification
    name: str


def get_conversion_context(*contracts: Contract) -> UnitConversionContext:
    """The conversion context that supports the units and currencies of the contracts provided"""
    # 1. Find the common parents between the contracts
    #    i. If no common parent exists, raise an exception
    # 2. Build the conversions up and down the chains identified.
    # 3. Populate the conversions in the unit context.
    # -  Currency unit conversions are done generically using a currency conversion context


## Example
#
# energy = ContractClassification(
#     name="energy",
#     parent=None,
#     supported_qty_units=("mwh", "btu", ...),
#     supported_currencies=('USD', 'EUR', 'GBP'),
#     qty_conversion_context=...
# )
#
# electricity = ContractClassification(
#     name='electricity',
#     parent=energy,
#     supported_qty_units=('kWh', ...),
#     supported_currencies=('USD', 'EUR', 'GBP'),
#     qty_conversion_context=...
# )
#
# oil = ContractClassification(
#     name='oil',
#     parent=energy,
#     supported_qty_units=('btu', ...),
#     supported_currencies=('USD', 'EUR', 'GBP'),
#     qty_conversion_context=...
# )