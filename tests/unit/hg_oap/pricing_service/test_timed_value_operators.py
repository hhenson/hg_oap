from datetime import datetime

import polars as pl
import pytest
from polars.testing import assert_frame_equal

from hg_oap.pricing_service import TimedValue
from hgraph import graph, TS, Frame
from hgraph.test import eval_node


@pytest.fixture
def timestamps() -> list[datetime]:
    return [datetime(2024, 7, 28), datetime(2024, 7, 29)]


@pytest.fixture
def lhs(timestamps) -> pl.DataFrame:
    return pl.DataFrame({"timestamp": timestamps, "val": [1.0, 2.0]})


@pytest.fixture
def rhs(timestamps) -> pl.DataFrame:
    return pl.DataFrame({"timestamp": timestamps, "val": [1.5, 2.5]})


def test_add_timed_value_frames(lhs, rhs):
    @graph
    def g(ts1: TS[Frame[TimedValue]], ts2: TS[Frame[TimedValue]]) -> TS[Frame[TimedValue]]:
        return ts1 + ts2

    expected = pl.DataFrame({"timestamp": [datetime(2024, 7, 28), datetime(2024, 7, 29)], "val": [2.5, 4.5]})

    out = eval_node(g, [lhs], [rhs])
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
