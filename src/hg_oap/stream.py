from dataclasses import fields, is_dataclass
from typing import get_origin, get_type_hints

from hgraph import CompoundScalar, TS, ts_schema
from hgraph.stream import (
    Stream as _HGraphStream,
    StreamStatus,
    combine_status_messages,
    combine_statuses,
    merge_join,
)

__all__ = (
    "Stream",
    "StreamStatus",
    "combine_status_messages",
    "combine_statuses",
    "merge_join",
)


class Stream:
    """Build an hgraph status stream around a schema or Python dataclass."""

    def __class_getitem__(cls, payload):
        payload_type = get_origin(payload) or payload
        if not (
            isinstance(payload_type, type)
            and is_dataclass(payload_type)
            and not issubclass(payload_type, CompoundScalar)
        ):
            return _HGraphStream[payload]

        payload_types = get_type_hints(payload_type)
        return ts_schema(
            **{field.name: TS[payload_types[field.name]] for field in fields(payload_type)},
            status=TS[StreamStatus],
            status_msg=TS[str],
        )
