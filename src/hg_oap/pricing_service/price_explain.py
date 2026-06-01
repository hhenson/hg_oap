import json
import logging
from dataclasses import dataclass
from datetime import datetime, date

from hg_oap.pricing_service import PriceType
from hg_oap.pricing_service.data_types import PricingModel, PricingRequest, PriceOpts
from hgraph import CompoundScalar

__all__ = ("PriceExplain", "PriceExplainMultiple", "PriceExplainTuple", "PriceExplainSingle", "PriceExplainTriplet",
           "PriceExplainLeaf", "render_price_explain", "render_price_explain_to_json")


logger = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class PriceExplain(CompoundScalar):
    """
    Tree structure defining the combination of component prices making up a price
    """
    symbol: str
    group_name: str = None
    origin: str = None
    price_type: PriceType = PriceType.NONE
    pricing_model: PricingModel = None
    narrative: str = None
    value: object = None
    timestamp: datetime = None
    weight: float = None
    pricing_request: PricingRequest = None
    opts: PriceOpts = None

    def __lt__(self, other):
        return _lt(self, other)

    def __gt__(self, other):
        return _gt(self, other)


@dataclass(frozen=True, kw_only=True)
class PriceExplainLeaf(PriceExplain):

    def ancestor_list(self):
        return ()

    def __repr__(self):
        return render_price_explain(self, 0)

    def __lt__(self, other):
        return _lt(self, other)

    def __gt__(self, other):
        return _gt(self, other)


@dataclass(frozen=True, kw_only=True)
class PriceExplainSingle(PriceExplain):
    ancestor: PriceExplain

    def ancestor_list(self):
        return (self.ancestor,)

    def __repr__(self):
        return render_price_explain(self, show_model_name=True)

    def __lt__(self, other):
        return _lt(self, other)

    def __gt__(self, other):
        return _gt(self, other)


@dataclass(frozen=True, kw_only=True)
class PriceExplainTuple(PriceExplain):
    ancestor1: PriceExplain
    ancestor2: PriceExplain

    def ancestor_list(self):
        return (self.ancestor1, self.ancestor2)

    def __repr__(self):
        return render_price_explain(self, show_model_name=True)

    def __lt__(self, other):
        return _lt(self, other)

    def __gt__(self, other):
        return _gt(self, other)


@dataclass(frozen=True, kw_only=True)
class PriceExplainTriplet(PriceExplain):
    ancestor1: PriceExplain
    ancestor2: PriceExplain
    ancestor3: PriceExplain

    def ancestor_list(self):
        return (self.ancestor1, self.ancestor2, self.ancestor3)

    def __repr__(self):
        return render_price_explain(self, show_model_name=True)

    def __lt__(self, other):
        return _lt(self, other)

    def __gt__(self, other):
        return _gt(self, other)


@dataclass(frozen=True, kw_only=True)
class PriceExplainMultiple(PriceExplain):
    ancestors: tuple[PriceExplain, ...]

    def ancestor_list(self):
        return self.ancestors

    def __repr__(self):
        return render_price_explain(self, show_model_name=True)

    def __lt__(self, other):
        return _lt(self, other)

    def __gt__(self, other):
        return _gt(self, other)


def render_price_explain(
    explain: PriceExplain,
    depth: int = 0,
    prices: dict[PricingRequest, float] = None,
    timestamps: dict[PricingRequest, datetime] = None,
    show_model_name: bool = False,
) -> str:
    if explain is None:
        return "<waiting...>"
    match depth:
        case 0:
            indent = ""
        case 1:
            indent = "--- "
        case _:
            indent = "---" * depth + " "
    if explain.value is not None:
        price = explain.value
    elif prices:
        price = prices.get(explain.pricing_request)
    else:
        price = None
    if explain.timestamp is not None:
        timestamp = explain.timestamp
    elif timestamps:
        timestamp = timestamps.get(explain.pricing_request)
    else:
        timestamp = None
    if price is not None and timestamp is not None:
        narrative = f": {format_price(price)} at {format_timestamp(timestamp)}"
    elif price is None:
        narrative = ""
    else:
        narrative = f": {format_price(price)}"
    narrative += f"; {explain.narrative}" if getattr(explain, "narrative", None) else ""
    if explain.weight is not None:
        narrative += f", weight {explain.weight}"
    if explain.opts in (None, PriceOpts()):
        explain_opts = ""
    else:
        explain_opts = f" {explain.opts}"
    origin_and_price_type = f" ({explain.price_type.name} price from {explain.origin})" if explain.origin else ""
    model_name = f" ({explain.pricing_model.__class__.__name__})" if show_model_name and explain.pricing_model else ""
    s = f"{indent}{explain.symbol}{explain_opts}{narrative}{origin_and_price_type}{model_name}"
    if explain.group_name:
        s += f"\n{indent}{explain.group_name}:"
    for a in explain.ancestor_list():
        if a is not None:
            s += f"\n{render_price_explain(a, depth + 1, prices, timestamps, show_model_name)}"
    return s


def render_price_explain_to_json(
    explain: PriceExplain,
    prices: dict[PricingRequest, object] = None,
    timestamps: dict[PricingRequest, datetime] = None,
    show_model_name: bool = False
) -> str:
    try:
        d = {explain.symbol: _price_explain_to_dict(explain, prices, timestamps, show_model_name)}
        return json.dumps(d)
    except:
        logger.exception(f"Failed to render price explain {explain} to json")
        return json.dumps({"error": "Error rendering price explain"})


def _price_explain_to_dict(
    explain: PriceExplain,
    prices: dict[PricingRequest, object] = None,
    timestamps: dict[PricingRequest, datetime] = None,
    show_model_name: bool = False
) -> dict:
    if explain is None:
        return {"explain": "..."}

    detail = {"model": explain.pricing_model.__class__.__name__} \
        if show_model_name and explain.pricing_model is not None \
        else {}
    if explain.opts not in (None, PriceOpts()):
        detail["opts"] = str(explain.opts)
    if explain.origin:
        detail["origin"] = explain.origin
    if explain.price_type not in (PriceType.NONE, None):
        detail["type"] = explain.price_type.name
    if explain.narrative:
        detail["explain"] = explain.narrative
    if explain.weight is not None:
        detail["weight"] = explain.weight
    price = prices.get(explain.pricing_request) if prices else None
    if explain.timestamp is not None:
        detail["time"] = format_timestamp(explain.timestamp)
    else:
        timestamp = timestamps.get(explain.pricing_request) if timestamps else None
        if timestamp is not None:
            detail["time"] = format_timestamp(timestamp)
    if explain.value is not None:
        detail["value"] = format_price(explain.value)
    elif price is not None:
        detail["value"] = format_price(price)

    if explain.group_name:
        group_detail = {}
        detail[explain.group_name] = group_detail
    else:
        group_detail = detail

    for a in explain.ancestor_list():
        if a is not None:
            group_detail[a.symbol] = _price_explain_to_dict(a, prices, timestamps, show_model_name)
    return detail


def format_timestamp(t: datetime) -> str:
    t = t.replace(microsecond=0)
    if t.date() != date.today():
        return f"{t} UTC"
    else:
        return f"{t.time()} UTC"


def format_price(price) -> str:
    if price.__class__ is float:
        return str(round(price, 6))
    else:
        return str(price)


def _lt(e1, e2):
    if e1.symbol.endswith("INDEX") and not e2.symbol.endswith("INDEX"):
        return True
    elif e2.symbol.endswith("INDEX") and not e1.symbol.endswith("INDEX"):
        return False
    else:
        return e1.symbol < e2.symbol


def _gt(e1, e2):
    if e2.symbol.endswith("INDEX") and not e1.symbol.endswith("INDEX"):
        return True
    elif e1.symbol.endswith("INDEX") and not e2.symbol.endswith("INDEX"):
        return False
    else:
        return e1.symbol > e2.symbol
