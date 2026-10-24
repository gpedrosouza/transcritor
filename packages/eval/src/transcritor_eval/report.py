"""Eval report models and renderers (JSON and Markdown)."""

from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from transcritor_eval.metrics_notation import NotationMetrics
from transcritor_eval.metrics_notes import NoteMetrics

HintsMode = Literal["instrument", "all"]
"""Hints given to the pipeline: only the instrument, or every hint in the manifest (key too)."""


class ItemResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: str
    status: Literal["ok", "skipped", "error"]
    message: str = ""
    notes: NoteMetrics | None = None
    notation: NotationMetrics | None = None


class EvalReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset: str
    subset: str
    pipeline: str
    hints: HintsMode
    created_at: datetime
    items: list[ItemResult]
    means: dict[str, float]  # keys like "notes.onset_f1"; mean over "ok" items only


def item_metrics(item: ItemResult) -> dict[str, float]:
    """Flatten an item's metrics into ``notes.<field>`` / ``notation.<field>`` keys."""
    flat: dict[str, float] = {}
    if item.notes is not None:
        flat |= {f"notes.{k}": v for k, v in item.notes.model_dump().items()}
    if item.notation is not None:
        flat |= {f"notation.{k}": v for k, v in item.notation.model_dump().items()}
    return flat


def to_json(report: EvalReport, path: Path) -> None:
    path.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")


_DASH = "\u2013"  # shown for metrics of non-ok rows


def _row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def to_markdown(report: EvalReport) -> str:
    keys = list(report.means)
    lines = [
        f"# Relatório de eval: {report.dataset}",
        "",
        f"- Dataset: {report.dataset}",
        f"- Subconjunto: {report.subset}",
        f"- Pipeline: {report.pipeline}",
        f"- Dicas: {report.hints}",
        f"- Data: {report.created_at.isoformat(timespec='seconds')}",
        "",
        _row(["item", "status", *keys]),
        _row(["---"] * (2 + len(keys))),
    ]
    for item in report.items:
        flat = item_metrics(item) if item.status == "ok" else {}
        cells = [f"{flat[k]:.3f}" if k in flat else _DASH for k in keys]
        lines.append(_row([item.item_id, item.status, *cells]))
    means = "".join(f" {report.means[k]:.3f} |" for k in keys)
    lines.append(f"| **média** | |{means}")
    for status, title in (("skipped", "Itens pulados"), ("error", "Erros")):
        group = [i for i in report.items if i.status == status]
        if group:
            lines += ["", f"## {title}", ""]
            lines += [f"- {i.item_id}: {i.message}" for i in group]
    return "\n".join(lines) + "\n"
