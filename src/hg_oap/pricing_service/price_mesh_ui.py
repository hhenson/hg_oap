from dataclasses import dataclass
from datetime import datetime
from typing import Tuple

from hgraph import operator, TS, TSB, graph, combine, str_, CompoundScalar, type_
from hgraph.adaptors.perspective import publish_multitable
from hgraph.stream.stream import Stream

from hg_oap.pricing_service import PRICE, Price, PriceOpts, PricingModel


@dataclass(frozen=True, kw_only=True)
class PriceUIView(CompoundScalar):
    price: float
    timestamp: datetime
    currency: str
    unit: str
    status: str
    price_type: str
    origin: str


@operator
def create_price_view(price: PRICE, model: TS[PricingModel]) -> TSB[PriceUIView]:
    ...


@graph(overloads=create_price_view, requires=lambda m, s: m[PRICE].py_type == TSB[Stream[Price]])
def create_price_view_live(price: PRICE, model: TS[PricingModel]) -> TSB[PriceUIView]:
    return combine[TSB[PriceUIView]](status=price.status_msg,
                                     price=price.val,
                                     unit=str_(price.unit),
                                     currency=str_(price.currency_unit),
                                     price_type=price.price_type.name,
                                     timestamp=price.timestamp,
                                     origin=price.origin)


@graph
def price_row_key(symbol: TS[str], model: TS[PricingModel], opts: TS[PriceOpts]) -> TS[Tuple[str, str, str]]:
    return combine[TS[Tuple[str, str, str]]](symbol, type_(model).name, str_(opts))


@graph
def publish_price_row(row_key: TS[Tuple[str, str, str]], row_data: TSB[PriceUIView]):
    publish_multitable("price_mesh", row_key, row_data, unique=True, index_col_name="symbol,model,opts", history=None)
