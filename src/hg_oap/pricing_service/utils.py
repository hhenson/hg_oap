import logging
from datetime import timedelta

from hgraph import graph, TS, filter_, const, log_, compute_node, TSL, SCALAR, SIZE

__all__ = ("combine_errors", "delayed_log")


@graph
def delayed_log(symbol: TS[str], error: TS[str], delay_seconds: int = 30):
    message = filter_(const(True, delay=timedelta(seconds=delay_seconds)), "{}: {}")
    do_log = (error != "")
    log_(filter_(do_log, message), filter_(do_log, symbol), filter_(do_log, error), level=logging.WARN)


@compute_node(valid=("symbol",), active=("errors",))
def combine_errors(symbol: TS[str], *errors: TSL[TS[SCALAR], SIZE]) -> TS[str]:
    error = ""
    for e in errors:
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
        if not all(e.value == "" for e in errors):
            return

    return error
