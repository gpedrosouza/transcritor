"""Score IR schema version and the single rule deciding which versions are supported."""

import re
from typing import Final

from transcritor_core.errors import SchemaVersionError

SCHEMA_VERSION: Final = "1.0.0"

_VERSION_RE = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")


def _parse_version(value: object) -> tuple[int, int, int] | None:
    if not isinstance(value, str):
        return None
    m = _VERSION_RE.fullmatch(value)
    if m is None:
        return None
    major, minor, patch = (int(g) for g in m.groups())
    return major, minor, patch


def check_supported_version(value: object) -> tuple[int, int, int]:
    """Return the parsed ``(major, minor, patch)`` of a supported schema version.

    Supported means a ``MAJOR.MINOR.PATCH`` string with the current major version and
    ``(minor, patch)`` not newer than ``SCHEMA_VERSION``. Anything else raises
    ``SchemaVersionError``.
    """
    parsed = _parse_version(value)
    current = _parse_version(SCHEMA_VERSION)
    if parsed is None or current is None or parsed[0] != current[0] or parsed[1:] > current[1:]:
        raise SchemaVersionError(
            f"unsupported schema_version '{value}' (supported: 1.x up to {SCHEMA_VERSION})",
            found=str(value),
        )
    return parsed
