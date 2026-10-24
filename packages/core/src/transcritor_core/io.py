"""Persistence of ScoreDoc as JSON, with schema version checking."""

import json
from collections.abc import Callable
from pathlib import Path

from pydantic import JsonValue

from transcritor_core.errors import SchemaVersionError
from transcritor_core.models import ScoreDoc
from transcritor_core.version import SCHEMA_VERSION, check_supported_version

# Maps a stored schema_version to a function upgrading a raw document to the next
# version. Empty while only 1.0.0 exists.
MIGRATIONS: dict[str, Callable[[dict[str, JsonValue]], dict[str, JsonValue]]] = {}


def migrate(raw: dict[str, JsonValue]) -> ScoreDoc:
    """Validate the document's schema version, upgrade it if needed, and parse it."""
    found = raw.get("schema_version")
    check_supported_version(found)
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
