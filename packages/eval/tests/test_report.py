import json
from datetime import UTC, datetime
from pathlib import Path

from transcritor_eval.metrics_notation import NotationMetrics
from transcritor_eval.metrics_notes import NoteMetrics
from transcritor_eval.report import EvalReport, ItemResult, to_json, to_markdown
from transcritor_eval.runner import run_eval

CI_MANIFEST = Path(__file__).resolve().parents[1] / "datasets" / "ci" / "manifest.json"


D = "\u2013"


def _report() -> EvalReport:
    notes = NoteMetrics(
        onset_precision=1.0, onset_recall=0.5, onset_f1=0.6667, offset_f1=0.25, downbeat_f1=0.0
    )
    notation = NotationMetrics(
        position_precision=1.0,
        position_recall=1.0,
        duration_accuracy=0.9,
        spelling_accuracy=0.8,
        accidental_accuracy=0.7,
        key_score=1.0,
        meter_accuracy=1.0,
    )
    return EvalReport(
        dataset="d",
        subset="full",
        pipeline="null",
        hints="instrument",
        created_at=datetime(2026, 10, 24, 12, 0, tzinfo=UTC),
        items=[
            ItemResult(item_id="a", status="ok", notes=notes, notation=notation),
            ItemResult(item_id="b", status="skipped", message="audio missing: /x/b.wav"),
            ItemResult(item_id="c", status="error", message="ValueError: kaput"),
        ],
        means={"notes.onset_f1": 0.6667, "notation.key_score": 1.0},
    )


def test_markdown_has_means_row() -> None:
    assert "| **média** |" in to_markdown(run_eval(CI_MANIFEST, "ci", "null"))


def test_markdown_layout() -> None:
    lines = to_markdown(_report()).splitlines()
    text = "\n".join(lines)
    assert "d" in lines[0] and "full" in text and "null" in text and "2026-10-24" in text
    assert "- Dicas: instrument" in lines
    assert "| item | status | notes.onset_f1 | notation.key_score |" in lines
    assert "| a | ok | 0.667 | 1.000 |" in lines
    assert f"| b | skipped | {D} | {D} |" in lines
    assert f"| c | error | {D} | {D} |" in lines
    assert "| **média** | | 0.667 | 1.000 |" in lines
    assert "audio missing: /x/b.wav" in text and "ValueError: kaput" in text
    assert "Itens pulados" in text and "Erros" in text


def test_markdown_omits_empty_sections() -> None:
    r = _report()
    r.items = r.items[:1]
    text = to_markdown(r)
    assert "Itens pulados" not in text and "Erros" not in text


def test_to_json_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "out.json"
    to_json(_report(), path)
    assert EvalReport.model_validate(json.loads(path.read_text(encoding="utf-8"))) == _report()
