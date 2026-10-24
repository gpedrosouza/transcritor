"""JSON Schema export of the ScoreDoc contract (source for the editor's TypeScript types)."""

import json
from pathlib import Path

from pydantic import JsonValue

from transcritor_core.models import ScoreDoc

# Assumes the package runs from the workspace checkout (src layout):
# <core>/src/transcritor_core/schema.py -> <core>/schema/scoredoc.schema.json.
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schema" / "scoredoc.schema.json"


def json_schema() -> dict[str, JsonValue]:
    """Return the JSON Schema of ScoreDoc (Op's schema arrives in F2)."""
    return ScoreDoc.model_json_schema(by_alias=True)


def main() -> None:
    """Regenerate the committed schema file."""
    SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCHEMA_PATH.write_text(json.dumps(json_schema(), indent=2) + "\n", encoding="utf-8")
