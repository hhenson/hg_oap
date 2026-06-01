from hg_oap.pricing_service import combine_errors
from hgraph import graph, TS
from hgraph.test import eval_node


def test_combine_errors():
    @graph
    def g(e1: TS[str], e2: TS[str], e3: TS[str]) -> TS[str]:
        return combine_errors("symbol", e1, e2, e3)

    results = eval_node(g, e1=["x", ""], e2=["y"], e3=["", "z"], __elide__=True)
    assert results == ["For symbol: x: y", "For symbol: y: z"]