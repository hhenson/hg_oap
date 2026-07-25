import types
import typing
from dataclasses import fields, is_dataclass

from hgraph import SCALAR, TS, TimeSeriesSchema
from hgraph._types import _substitute_typevars
from hgraph.stream.stream import (
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


_DATACLASS_STREAM_SCHEMAS: dict[object, type[TimeSeriesSchema]] = {}


def _schema_token(value):
    origin = typing.get_origin(value)
    if origin is not None:
        arguments = ",".join(_schema_token(argument) for argument in typing.get_args(value))
        return f"{origin.__module__}.{origin.__qualname__}[{arguments}]"
    if isinstance(value, type):
        return f"{value.__module__}.{value.__qualname__}"
    return repr(value)


class Stream:
    """Build an hgraph status stream around a schema or Python dataclass."""

    def __class_getitem__(cls, payload):
        try:
            return _HGraphStream[payload]
        except TypeError:
            pass

        cached = _DATACLASS_STREAM_SCHEMAS.get(payload)
        if cached is not None:
            return cached

        origin = typing.get_origin(payload) or payload
        is_open_scalar = payload is SCALAR
        if not is_open_scalar and not (
            isinstance(origin, type) and is_dataclass(origin)
        ):
            raise TypeError(
                "Stream[...] requires a dataclass, CompoundScalar, or "
                f"TimeSeriesSchema payload, got {payload!r}"
            )

        parameters = (
            tuple(getattr(origin, "__parameters__", ())) if not is_open_scalar else ()
        )
        arguments = tuple(typing.get_args(payload))
        if arguments and len(arguments) != len(parameters):
            raise TypeError(
                f"{origin.__qualname__} expects {len(parameters)} type arguments, "
                f"got {len(arguments)}"
            )
        substitutions = dict(zip(parameters, arguments))

        annotations = {
            "status": TS[StreamStatus],
            "status_msg": TS[str],
        }
        if not is_open_scalar:
            resolved_annotations = typing.get_type_hints(origin)
            for item in fields(origin):
                annotations[item.name] = TS[
                    _substitute_typevars(
                        resolved_annotations.get(item.name, item.type), substitutions
                    )
                ]

        schema = types.new_class(
            f"Stream[{_schema_token(payload)}]", (TimeSeriesSchema,)
        )
        schema.__module__ = __name__
        schema.__annotations__ = annotations
        _DATACLASS_STREAM_SCHEMAS[payload] = schema
        return schema
