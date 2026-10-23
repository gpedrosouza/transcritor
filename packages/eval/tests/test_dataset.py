import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from transcritor_eval.dataset import Manifest, load_manifest, read_reference_notes, resolve_audio

DATASETS = Path(__file__).resolve().parents[1] / "datasets"
CI_MANIFEST = DATASETS / "ci" / "manifest.json"
MONO_V1_MANIFEST = DATASETS / "mono-v1" / "manifest.json"


def test_ci_manifest_loads_and_resolves() -> None:
    m = load_manifest(CI_MANIFEST)
    item = m.items[0]
    assert item.instrument == "flute" and "ci" in item.subsets
    assert resolve_audio(CI_MANIFEST, m, item, Path("data")).exists()
    assert len(read_reference_notes(CI_MANIFEST.parent / item.reference_notes)) == 8


def test_resolve_audio_data_root() -> None:
    m = load_manifest(CI_MANIFEST)
    m2 = Manifest(name="x", audio_root="data", items=m.items)
    got = resolve_audio(CI_MANIFEST, m2, m2.items[0], Path("/some/data"))
    assert got == Path("/some/data") / m2.items[0].audio


def test_manifest_rejects_unknown_instrument(tmp_path: Path) -> None:
    raw = json.loads(CI_MANIFEST.read_text())
    raw["items"][0]["instrument"] = "kazoo"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(raw))
    with pytest.raises(ValidationError, match="kazoo"):
        load_manifest(path)


def test_mono_v1_manifest_is_valid() -> None:
    assert load_manifest(MONO_V1_MANIFEST).audio_root == "data"
