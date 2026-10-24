"""Exact rational type for musical time, usable in Pydantic models."""

import re
from fractions import Fraction
from typing import Annotated, Any

from pydantic import BeforeValidator, PlainSerializer, WithJsonSchema

_FRACTION_RE = re.compile(r"^-?\d+(/\d+)?$")


def _parse(value: Any) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return Fraction(value)
    if isinstance(value, str) and _FRACTION_RE.match(value):
        try:
            return Fraction(value)
        except ZeroDivisionError:
            raise ValueError("fraction denominator must not be zero") from None
    raise ValueError(f"invalid musical fraction: {value!r}")


MusicalFraction = Annotated[
    Fraction,
    BeforeValidator(_parse),
    PlainSerializer(str, return_type=str),
    WithJsonSchema({"type": "string", "pattern": r"^-?\d+(/\d+)?$"}),
]
