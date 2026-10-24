import json

from transcritor_core.schema import SCHEMA_PATH, json_schema


def test_committed_schema_is_current() -> None:
    committed = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert committed == json_schema(), "run: uv run transcritor-schema"
