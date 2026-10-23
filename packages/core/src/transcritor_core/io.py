"""Persistence of ScoreDoc as JSON, with schema version checking."""

import json
import re
from collections.abc import Callable
from pathlib import Path

from pydantic import JsonValue

from transcritor_core.errors import SchemaVersionError
from transcritor_core.models import SCHEMA_VERSION, ScoreDoc

_VERSION_RE = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")

# Maps a stored schema_version to a function upgrading a raw document to the next
# version. Empty while only 1.0.0 exists.
MIGRATIONS: dict[str, Callable[[dict[str, JsonValue]], dict[str, JsonValue]]] = {}


def _parse_version(value: object) -> tuple[int, int, int] | None:
    if not isinstance(value, str):
        return None
    m = _VERSION_RE.fullmatch(value)
    if m is None:
        return None
    major, minor, patch = (int(g) for g in m.groups())
    return major, minor, patch


def migrate(raw: dict[str, JsonValue]) -> ScoreDoc:
    """Validate the document's schema version, upgrade it if needed, and parse it."""
    found = raw.get("schema_version")
    parsed = _parse_version(found)
    current = _parse_version(SCHEMA_VERSION)
    if parsed is None or current is None or parsed[0] != current[0] or parsed[1:] > current[1:]:
        raise SchemaVersionError(
            f"unsupported schema_version '{found}' (supported: 1.x up to {SCHEMA_VERSION})",
            found=str(found),
        )
    while isinstance(version := raw.get("schema_version"), str) and version in MIGRATIONS:
        raw = MIGRATIONS[version](raw)
    return ScoreDoc.model_validate(raw)


def dump(doc: ScoreDoc, path: Path) -> None:
    """Write the document as UTF-8 JSON indented with 2 spaces."""
    path.write_text(doc.model_dump_json(indent=2, by_alias=True) + "\n", encoding="utf-8")


def load(path: Path) -> ScoreDoc:
    """Read a document from disk, migrating it to the current schema version."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SchemaVersionError(
            f"unsupported schema_version 'None' (supported: 1.x up to {SCHEMA_VERSION})",
            found="None",
        )
    return migrate(data)
