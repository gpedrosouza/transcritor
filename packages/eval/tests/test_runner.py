import json
import shutil
from pathlib import Path

import pytest
import transcritor_eval.runner as runner_mod
from transcritor_core import Hints, KeyHint, ScoreDoc
from transcritor_eval.metrics_notation import NotationMetrics
from transcritor_eval.metrics_notes import NoteMetrics
from transcritor_eval.pipelines import PIPELINES, null_pipeline
from transcritor_eval.runner import run_eval

DATASETS = Path(__file__).resolve().parents[1] / "datasets"
CI_DIR = DATASETS / "ci"
CI_MANIFEST = CI_DIR / "manifest.json"
CI_WAV = CI_DIR / "audio" / "c_major_scale_flute.wav"

MEAN_KEYS = [f"notes.{f}" for f in NoteMetrics.model_fields] + [
    f"notation.{f}" for f in NotationMetrics.model_fields
]


def manifest_with_missing_audio(tmp_path: Path, subsets: list[str] | None = None) -> Path:
    """Write a manifest in ``tmp_path`` whose only item points at a missing wav."""
    shutil.copytree(CI_DIR / "refs", tmp_path / "refs")
    data = json.loads(CI_MANIFEST.read_text(encoding="utf-8"))
    data["audio_root"] = "data"
    item = data["items"][0]
    item["audio"] = "missing.wav"
    item["subsets"] = subsets if subsets is not None else ["full"]
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_null_pipeline_on_ci_set_runs_and_scores_zero() -> None:
    r = run_eval(CI_MANIFEST, "ci", "null")
    assert [i.status for i in r.items] == ["ok"]
    assert r.means["notes.onset_f1"] == 0.0
    assert list(r.means) == MEAN_KEYS
    assert r.created_at.tzinfo is not None
    assert r.dataset == "ci" and r.subset == "ci" and r.pipeline == "null"


def _recording_pipeline(monkeypatch: pytest.MonkeyPatch) -> list[Hints]:
    received: list[Hints] = []

    def recording(audio_path: Path, hints: Hints) -> ScoreDoc:
        received.append(hints)
        return null_pipeline(audio_path, hints)

    monkeypatch.setitem(PIPELINES, "recording", recording)
    return received


def test_default_run_passes_only_the_instrument_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    received = _recording_pipeline(monkeypatch)
    r = run_eval(CI_MANIFEST, "ci", "recording")
    assert r.hints == "instrument"
    assert [h.key for h in received] == [None]
    assert [i.instrument for i in received[0].instruments] == ["flute"]


def test_hints_all_passes_the_reference_key(monkeypatch: pytest.MonkeyPatch) -> None:
    received = _recording_pipeline(monkeypatch)
    r = run_eval(CI_MANIFEST, "ci", "recording", hints="all")
    assert r.hints == "all"
    assert received[0].key == KeyHint(tonic_step="C", tonic_alter=0, mode="major")


def test_null_pipeline_builds_document_with_provenance() -> None:
    from transcritor_core import InstrumentCount

    hints = Hints(
        instruments=[
            InstrumentCount(instrument="flute", count=1),
            InstrumentCount(instrument="violin", count=2),
        ]
    )
    doc = null_pipeline(CI_WAV, hints)
    assert [p.id for p in doc.parts] == ["p1", "p2"]
    assert doc.source.audio.original_name == "c_major_scale_flute.wav"
    assert len(doc.source.audio.sha256) == 64
    assert doc.source.audio.duration_s > 0
    assert [p.stage for p in doc.provenance] == ["null"]
    assert PIPELINES["null"] is null_pipeline


def test_missing_audio_is_skipped_in_full(tmp_path: Path) -> None:
    r = run_eval(manifest_with_missing_audio(tmp_path), "full", "null", data_root=tmp_path)
    assert r.items[0].status == "skipped" and "missing.wav" in r.items[0].message
    assert r.means == {}


def test_missing_audio_fails_in_ci(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        run_eval(
            manifest_with_missing_audio(tmp_path, subsets=["ci"]),
            "ci",
            "null",
            data_root=tmp_path,
        )


def test_items_outside_subset_are_not_listed(tmp_path: Path) -> None:
    r = run_eval(manifest_with_missing_audio(tmp_path, subsets=["ci"]), "full", "null")
    assert r.items == []
    assert r.means == {}


def test_unknown_pipeline_lists_valid_names() -> None:
    with pytest.raises(KeyError, match="null"):
        run_eval(CI_MANIFEST, "ci", "nope")


def test_pipeline_exception_becomes_error_item(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(audio_path: Path, hints: Hints) -> ScoreDoc:
        raise ValueError("kaput")

    monkeypatch.setitem(PIPELINES, "boom", boom)
    r = run_eval(CI_MANIFEST, "ci", "boom")
    assert r.items[0].status == "error"
    assert r.items[0].message == "ValueError: kaput"
    assert r.items[0].notes is None
    assert r.means == {}


def test_metric_exception_becomes_error_item(monkeypatch: pytest.MonkeyPatch) -> None:
    def bad(*args: object, **kwargs: object) -> NotationMetrics:
        raise RuntimeError("bad score")

    monkeypatch.setattr(runner_mod, "notation_metrics", bad)
    r = run_eval(CI_MANIFEST, "ci", "null")
    assert r.items[0].status == "error"
    assert r.items[0].message == "RuntimeError: bad score"
