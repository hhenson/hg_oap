from typing import Callable, Any

from multimethod import parametric

from hg_oap.units import Unit
from hg_oap.units.default_unit_system import U
from hgraph import HgCompoundScalarType
from hgraph._impl._operators._to_json import to_json_converter, from_json_converter

UnitType = parametric(HgCompoundScalarType, lambda x: x.py_type is Unit)

@to_json_converter.register
def _(value: UnitType, delta=False) -> Callable[[Any], str]:
    return lambda v: f'"{v.name}"'

@from_json_converter.register
def _(value: UnitType, delta=False) -> Callable[[dict], Any]:
    d = {k: v for k, v in vars(U).items() if not k.startswith("__") and isinstance(v, Unit)}
    return lambda v: d.get(v, U.NONE) if v else U.NONE
