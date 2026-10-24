import json
from collections.abc import Callable
from pathlib import Path

import pytest
from transcritor_core.errors import SchemaVersionError
from transcritor_core.io import dump, load, migrate
from transcritor_core.models import ScoreDoc


def test_roundtrip(tmp_path: Path, make_doc_with_notation: Callable[[], ScoreDoc]) -> None:
    doc = make_doc_with_notation()
    dump(doc, tmp_path / "d.json")
    assert load(tmp_path / "d.json") == doc


def test_dump_is_indented_utf8_with_fraction_strings(
    tmp_path: Path, make_doc_with_notation: Callable[[], ScoreDoc]
) -> None:
    doc = make_doc_with_notation()
    doc.source.audio.original_name = "sonâta.wav"
    dump(doc, tmp_path / "d.json")
    text = (tmp_path / "d.json").read_text(encoding="utf-8")
    assert '\n  "schema_version"' in text
    assert "sonâta.wav" in text
    assert '"beat": "1/3"' in text


@pytest.mark.parametrize("v", ["2.0.0", "0.9.0", "1.1.0", "1.0.1", "1.x", "abc", "1.0", None, 1])
def test_unsupported_version(make_doc: Callable[[], ScoreDoc], v: object) -> None:
    raw = make_doc().model_dump(mode="json")
    raw["schema_version"] = v
    with pytest.raises(SchemaVersionError, match=r"supported: 1\.x up to 1\.0\.0") as exc:
        migrate(raw)
    assert exc.value.found == str(v)
    assert f"unsupported schema_version '{v}'" in str(exc.value)


def test_missing_version(make_doc: Callable[[], ScoreDoc]) -> None:
    raw = make_doc().model_dump(mode="json")
    del raw["schema_version"]
    with pytest.raises(SchemaVersionError, match="'None'"):
        migrate(raw)


def test_migrate_current_version(make_doc: Callable[[], ScoreDoc]) -> None:
    doc = make_doc()
    assert migrate(json.loads(doc.model_dump_json())) == doc
