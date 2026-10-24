"""Eval runner: executes a pipeline over a dataset subset and scores it."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from transcritor_core import Hints, InstrumentCount

from transcritor_eval.align import read_downbeats
from transcritor_eval.dataset import load_manifest, read_reference_notes, resolve_audio
from transcritor_eval.measures import reference_downbeats
from transcritor_eval.metrics_notation import NotationMetrics, notation_metrics
from transcritor_eval.metrics_notes import NoteMetrics, note_metrics
from transcritor_eval.pipelines import PIPELINES, Pipeline
from transcritor_eval.report import EvalReport, HintsMode, ItemResult, item_metrics

__all__ = ["EvalReport", "ItemResult", "run_eval"]


def _means(items: list[ItemResult]) -> dict[str, float]:
    ok = [item_metrics(i) for i in items if i.status == "ok"]
    if not ok:
        return {}
    return {k: sum(m[k] for m in ok) / len(ok) for k in ok[0]}


def run_eval(
    manifest_path: Path,
    subset: Literal["ci", "full"],
    pipeline_name: str,
    data_root: Path = Path("data/eval/audio"),
    hints: HintsMode = "instrument",
) -> EvalReport:
    """Run ``pipeline_name`` on every item of ``subset`` and score it.

    ``hints="instrument"`` (default) gives the pipeline only the item's instrument, so the
    key is estimated, not handed over; ``hints="all"`` also passes the reference key.
    """
    if pipeline_name not in PIPELINES:
        raise KeyError(f"unknown pipeline {pipeline_name!r}; valid: {sorted(PIPELINES)}")
    pipeline: Pipeline = PIPELINES[pipeline_name]
    manifest = load_manifest(manifest_path)
    base = manifest_path.parent
    results: list[ItemResult] = []
    for item in manifest.items:
        if subset not in item.subsets:
            continue
        audio = resolve_audio(manifest_path, manifest, item, data_root)
        if not audio.is_file():
            if subset == "ci":
                raise FileNotFoundError(f"CI audio missing for {item.id}: {audio}")
            results.append(
                ItemResult(item_id=item.id, status="skipped", message=f"audio not found: {audio}")
            )
            continue
        item_hints = Hints(
            instruments=[InstrumentCount(instrument=item.instrument, count=1)],
            key=item.key if hints == "all" else None,
        )
        try:
            doc = pipeline(audio, item_hints)
            notes: NoteMetrics = note_metrics(
                read_reference_notes(base / item.reference_notes),
                reference_downbeats(
                    base / item.reference_score, read_downbeats(base / item.reference_downbeats)
                ),
                doc,
            )
            notation: NotationMetrics = notation_metrics(base / item.reference_score, item.key, doc)
        except Exception as e:
            results.append(
                ItemResult(item_id=item.id, status="error", message=f"{type(e).__name__}: {e}")
            )
            continue
        results.append(ItemResult(item_id=item.id, status="ok", notes=notes, notation=notation))
    return EvalReport(
        dataset=manifest.name,
        subset=subset,
        pipeline=pipeline_name,
        hints=hints,
        created_at=datetime.now(UTC),
        items=results,
        means=_means(results),
    )
