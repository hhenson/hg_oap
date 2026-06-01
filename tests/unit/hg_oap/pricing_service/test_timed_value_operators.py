from datetime import datetime

import polars as pl
import pytest
from polars.testing import assert_frame_equal

from hg_oap.pricing_service import TimedValue
from hgraph import TS, Frame, abs_, add_, graph, sub_
from hgraph.test import eval_node


@pytest.fixture
def timestamps() -> list[datetime]:
    return [datetime(2024, 7, 28), datetime(2024, 7, 29)]


@pytest.fixture
def timestamps2() -> list[datetime]:
    return [datetime(2024, 7, 28), datetime(2024, 7, 29), datetime(2024, 7, 30)]


@pytest.fixture
def timestamps3() -> list[datetime]:
    return [datetime(2024, 7, 29), datetime(2024, 7, 30), datetime(2024, 7, 31)]


@pytest.fixture
def lhs(timestamps) -> pl.DataFrame:
    return pl.DataFrame({"timestamp": timestamps, "val": [1.0, 2.0]})

@pytest.fixture
def lhs2(timestamps2) -> pl.DataFrame:
    return pl.DataFrame({"timestamp": timestamps2, "val": [1.0, 2.0, 3.0]})


@pytest.fixture
def rhs(timestamps) -> pl.DataFrame:
    return pl.DataFrame({"timestamp": timestamps, "val": [1.5, 2.5]})


@pytest.fixture
def rhs2(timestamps2) -> pl.DataFrame:
    return pl.DataFrame({"timestamp": timestamps2, "val": [1.5, 2.5, 3.5]})


@pytest.fixture
def rhs3(timestamps3) -> pl.DataFrame:
    return pl.DataFrame({"timestamp": timestamps3, "val": [1.5, 2.5, 3.5]})


def test_add_timed_value_frames(lhs, rhs):
    @graph
    def g(ts1: TS[Frame[TimedValue]], ts2: TS[Frame[TimedValue]]) -> TS[Frame[TimedValue]]:
        return ts1 + ts2

    expected = pl.DataFrame({"timestamp": [datetime(2024, 7, 28), datetime(2024, 7, 29)], "val": [2.5, 4.5]})

    out = eval_node(g, [lhs], [rhs])
    assert_frame_equal(out[0], expected)


def test_add_timed_value_frames2(lhs, rhs2):
    @graph
    def g(ts1: TS[Frame[TimedValue]], ts2: TS[Frame[TimedValue]]) -> TS[Frame[TimedValue]]:
        return add_(ts1, ts2, __strict__=False)

    expected = pl.DataFrame({"timestamp": [datetime(2024, 7, 28), datetime(2024, 7, 29), datetime(2024, 7, 30)], "val": [2.5, 4.5, 3.5]})

    out = eval_node(g, [lhs], [rhs2])
    assert_frame_equal(out[0], expected)


def test_add_timed_value_frames3(lhs2, rhs):
    @graph
    def g(ts1: TS[Frame[TimedValue]], ts2: TS[Frame[TimedValue]]) -> TS[Frame[TimedValue]]:
        return add_(ts1, ts2, __strict__=False)

    expected = pl.DataFrame({"timestamp": [datetime(2024, 7, 28), datetime(2024, 7, 29), datetime(2024, 7, 30)], "val": [2.5, 4.5, 3.0]})

    out = eval_node(g, [lhs2], [rhs])
    assert_frame_equal(out[0], expected)


def test_mul_timed_value_frames(lhs, rhs):
    @graph
    def g(ts1: TS[Frame[TimedValue]], ts2: TS[Frame[TimedValue]]) -> TS[Frame[TimedValue]]:
        return ts1 * ts2

    expected = pl.DataFrame({"timestamp": [datetime(2024, 7, 28), datetime(2024, 7, 29)], "val": [1.5, 5.0]})

    out = eval_node(g, [lhs], [rhs])
    assert_frame_equal(out[0], expected)


def test_mul_timed_value_frame(lhs):
    @graph
    def g(ts1: TS[Frame[TimedValue]], ts2: TS[float]) -> TS[Frame[TimedValue]]:
        return ts1 * ts2

    expected = pl.DataFrame({"timestamp": [datetime(2024, 7, 28), datetime(2024, 7, 29)], "val": [2.0, 4.0]})

    out = eval_node(g, [lhs], [2.0])
    assert_frame_equal(out[0], expected)


def test_div_timed_value_frame(lhs):
    @graph
    def g(ts1: TS[Frame[TimedValue]], ts2: TS[float]) -> TS[Frame[TimedValue]]:
        return ts1 / ts2

    expected = pl.DataFrame({"timestamp": [datetime(2024, 7, 28), datetime(2024, 7, 29)], "val": [0.5, 1.0]})

    out = eval_node(g, [lhs], [2.0])
    assert_frame_equal(out[0], expected)


def test_sub_timed_value_frame(lhs, rhs):
    @graph
    def g(ts1: TS[Frame[TimedValue]], ts2: TS[Frame[TimedValue]]) -> TS[Frame[TimedValue]]:
        return ts1 - ts2

    expected = pl.DataFrame({"timestamp": [datetime(2024, 7, 28), datetime(2024, 7, 29)], "val": [-0.5, -0.5]})

    out = eval_node(g, [lhs], [rhs])
    assert_frame_equal(out[0], expected)


def test_sub_timed_value_frame_empty_lhs(rhs):
    @graph
    def g(ts1: TS[Frame[TimedValue]], ts2: TS[Frame[TimedValue]]) -> TS[Frame[TimedValue]]:
        return ts1 - ts2

    expected = pl.DataFrame({"timestamp": [datetime(2024, 7, 28), datetime(2024, 7, 29)], "val": [-1.5, -2.5]})

    out = eval_node(g, [pl.DataFrame()], [rhs])
    assert_frame_equal(out[0], expected)


def test_sub_timed_value_frame_empty_rhs(lhs):
    @graph
    def g(ts1: TS[Frame[TimedValue]], ts2: TS[Frame[TimedValue]]) -> TS[Frame[TimedValue]]:
        return ts1 - ts2

    expected = pl.DataFrame({"timestamp": [datetime(2024, 7, 28), datetime(2024, 7, 29)], "val": [1.0, 2.0]})

    out = eval_node(g, [lhs], [pl.DataFrame()])
    assert_frame_equal(out[0], expected)


def test_abs_timed_value_frame(timestamps):
    df = pl.DataFrame({"timestamp": timestamps, "val": [1.0, -2.0]})
    expected = pl.DataFrame({"timestamp": timestamps, "val": [1.0, 2.0]})

    @graph
    def g(ts: TS[Frame[TimedValue]]) -> TS[Frame[TimedValue]]:
        return abs_(ts)

    out = eval_node(g, [df])
    assert_frame_equal(out[0], expected)


def test_sub_timed_value_frame_maintain_sort_order(lhs2, rhs3):
    @graph
    def g(ts1: TS[Frame[TimedValue]], ts2: TS[Frame[TimedValue]]) -> TS[Frame[TimedValue]]:
        return sub_(ts1, ts2, __strict__=False)

    expected = pl.DataFrame(
        {
            "timestamp": [datetime(2024, 7, 28), datetime(2024, 7, 29), datetime(2024, 7, 30), datetime(2024, 7, 31)],
            "val": [1.0, 0.5, 0.5, -3.5]
        }
    )

    out = eval_node(g, [lhs2], [rhs3])
    assert_frame_equal(out[0], expected)


def test_add_timed_value_frame_maintain_sort_order(lhs2, rhs3):
    @graph
    def g(ts1: TS[Frame[TimedValue]], ts2: TS[Frame[TimedValue]]) -> TS[Frame[TimedValue]]:
        return add_(ts1, ts2, __strict__=False)

    expected = pl.DataFrame(
        {
            "timestamp": [datetime(2024, 7, 28), datetime(2024, 7, 29), datetime(2024, 7, 30), datetime(2024, 7, 31)],
            "val": [1.0, 3.5, 5.5, 3.5]
        }
    )

    out = eval_node(g, [lhs2], [rhs3])
    assert_frame_equal(out[0], expected)