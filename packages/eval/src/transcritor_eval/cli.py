"""``transcritor-eval`` command line: run, gate, baseline, align."""

import argparse
import json
import math
import sys
from pathlib import Path

from transcritor_eval.align import read_downbeats, reference_notes_from_score
from transcritor_eval.dataset import write_reference_notes
from transcritor_eval.gate import compare
from transcritor_eval.pipelines import PIPELINES
from transcritor_eval.report import EvalReport, to_json, to_markdown
from transcritor_eval.runner import run_eval


def _load_report(path: Path) -> EvalReport:
    return EvalReport.model_validate_json(path.read_text(encoding="utf-8"))


def _load_baseline(path: Path) -> dict[str, float]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: baseline must be a JSON object")
    baseline: dict[str, float] = {}
    for key, value in raw.items():
        if (
            isinstance(value, bool)
            or not isinstance(value, int | float)
            or not math.isfinite(value)
        ):
            raise ValueError(f"{path}: baseline value for {key!r} is not a finite number")
        baseline[str(key)] = float(value)
    return baseline


def _cmd_run(args: argparse.Namespace) -> int:
    report = run_eval(args.manifest, args.subset, args.pipeline, args.data_root)
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    to_json(report, out / "report.json")
    md_path = out / "report.md"
    md_path.write_text(to_markdown(report), encoding="utf-8")
    counts = {s: sum(i.status == s for i in report.items) for s in ("ok", "skipped", "error")}
    print(md_path)
    print(f"{counts['ok']} ok, {counts['skipped']} skipped, {counts['error']} error")
    return 0


def _cmd_gate(args: argparse.Namespace) -> int:
    report = _load_report(args.report)
    baseline = _load_baseline(args.baseline)
    failed = False
    for item in report.items:
        if item.status == "error":
            print(f"ERROR {item.item_id}: {item.message}")
            failed = True
    for r in compare(report, baseline, args.tolerance):
        print(f"REGRESSION {r.metric}: baseline {r.baseline:.3f} -> current {r.current:.3f}")
        failed = True
    if failed:
        return 1
    print("OK: no regressions")
    return 0


def _cmd_baseline(args: argparse.Namespace) -> int:
    report = _load_report(args.report)
    problems: list[str] = []
    if not report.means:
        problems.append("report has no means")
    problems += [
        f"non-finite mean for {k}" for k, v in report.means.items() if not math.isfinite(v)
    ]
    problems += [
        f"item {i.item_id} is {i.status}: {i.message}" for i in report.items if i.status != "ok"
    ]
    if problems:
        print("refusing to write baseline:", *problems, sep="\n  ", file=sys.stderr)
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report.means, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


def _cmd_align(args: argparse.Namespace) -> int:
    notes = reference_notes_from_score(args.score, read_downbeats(args.downbeats), args.part)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    write_reference_notes(notes, args.out)
    return 0


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="transcritor-eval")
    sub = p.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run a pipeline over a dataset and write the report")
    run.add_argument("--manifest", type=Path, required=True)
    run.add_argument("--subset", choices=["ci", "full"], required=True)
    run.add_argument("--pipeline", choices=sorted(PIPELINES), required=True)
    run.add_argument("--data-root", type=Path, default=Path("data/eval/audio"))
    run.add_argument("--out", type=Path, required=True)
    run.set_defaults(func=_cmd_run)

    gate = sub.add_parser("gate", help="fail when a report regresses against a baseline")
    gate.add_argument("--report", type=Path, required=True)
    gate.add_argument("--baseline", type=Path, required=True)
    gate.add_argument("--tolerance", type=float, default=0.01)
    gate.set_defaults(func=_cmd_gate)

    base = sub.add_parser("baseline", help="write a report's means as a new baseline")
    base.add_argument("--report", type=Path, required=True)
    base.add_argument("--out", type=Path, required=True)
    base.set_defaults(func=_cmd_baseline)

    align = sub.add_parser("align", help="derive reference notes CSV from a score")
    align.add_argument("score", type=Path)
    align.add_argument("downbeats", type=Path)
    align.add_argument("--out", type=Path, required=True)
    align.add_argument("--part", type=int, default=0)
    align.set_defaults(func=_cmd_align)
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        code: int = args.func(args)
    except (OSError, ValueError) as exc:  # bad user input: missing file, malformed JSON
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return code
