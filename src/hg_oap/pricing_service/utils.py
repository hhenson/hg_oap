import logging
from datetime import timedelta

from hgraph import graph, TS, filter_, const, log_, compute_node

__all__ = ("combine_errors", "delayed_log")


@graph
def delayed_log(symbol: TS[str], error: TS[str], delay_seconds: int = 5):
    message = filter_(const(True, delay=timedelta(seconds=delay_seconds)), "{}: {}")
    log_(filter_(error != "", message), symbol, error, level=logging.WARN)


@compute_node(valid=("symbol",), active=("error1", "error2", "error3"))
def combine_errors(symbol: TS[str], error1: TS[str], error2: TS[str] = "", error3: TS[str] = "") -> TS[str]:
    error = ""
    for e in (error1, error2, error3):
        if e.valid and e.value not in error:
            if error:
                error += ": " + e.value
            else:
                error = e.value

    if error:
        if symbol.value not in error:
            error = f"For {symbol.value}: " + error
    else:
        # If we have no errors, ensure all errors are valid before returning to avoid sending OK statuses before
        # we know everything
        if not all(e.value == "" for e in (error1, error2, error3)):
            return

    return error
