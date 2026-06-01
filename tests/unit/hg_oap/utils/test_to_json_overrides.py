import pytest

from hg_oap.units import Quantity
from hg_oap.utils.to_json_overrides import *
from hgraph import to_json, TS, from_json
from hgraph.test import eval_node


@pytest.mark.parametrize(
    ["tp", "ts", "expected"],
    [[TS[Unit], U.cm, '"cm"'],
     [TS[Quantity], 12.0 * U.bbl, '{"qty": 12.0, "unit": "bbl"}']
     ])
def test_to_json(tp, ts, expected):
    assert eval_node(to_json[tp],[ts]) == [expected]
    assert eval_node(from_json[tp], [expected]) == [ts]