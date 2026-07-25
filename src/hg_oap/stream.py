from dataclasses import fields, FrozenInstanceError, is_dataclass
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
        if (
            isinstance(payload_type, type)
            and is_dataclass(payload_type)
            and not issubclass(payload_type, CompoundScalar)
        ):
            payload_fields = fields(payload_type)
            probe = object.__new__(payload_type)
            probe_field = payload_fields[0].name if payload_fields else "_frozen_probe"
            try:
                setattr(probe, probe_field, None)
            except FrozenInstanceError:
                pass
            else:
                raise TypeError(f"Stream payload dataclass must be frozen, got {payload!r}")

            payload_types = get_type_hints(payload_type)
            return ts_schema(
                **{field.name: TS[payload_types[field.name]] for field in payload_fields},
                status=TS[StreamStatus],
                status_msg=TS[str],
            )

        return _HGraphStream[payload]
