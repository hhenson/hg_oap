from dataclasses import dataclass

from hg_oap.instruments.instrument import Instrument
from hgraph import TS, TSB, subscription_service
from hgraph.stream import Stream


@dataclass(frozen=True)
class InstrumentData:
    instrument: Instrument


@subscription_service
def instrument_by_name(key: TS[str], path: str = "instrument") -> TSB[Stream[InstrumentData]]:
    """
    Service provides the instrument corresponding to the given symbol
    A status stream is also returned
    """
