import math
from datetime import UTC, datetime

from transcritor_eval.gate import compare
from transcritor_eval.report import EvalReport


def report_with(means: dict[str, float]) -> EvalReport:
    return EvalReport(
        dataset="d",
        subset="ci",
        pipeline="null",
        hints="instrument",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        items=[],
        means=means,
    )


def test_no_regression_within_tolerance() -> None:
    assert compare(report_with({"notes.onset_f1": 0.795}), {"notes.onset_f1": 0.80}) == []


def test_regression_detected() -> None:
    [r] = compare(report_with({"notes.onset_f1": 0.70}), {"notes.onset_f1": 0.80})
    assert r.metric == "notes.onset_f1"
    assert r.baseline == 0.80 and r.current == 0.70


def test_missing_metric_is_regression() -> None:
    [r] = compare(report_with({}), {"notes.onset_f1": 0.8})
    assert math.isnan(r.current)


def test_nan_metric_is_regression() -> None:
    [r] = compare(report_with({"notes.onset_f1": float("nan")}), {"notes.onset_f1": 0.8})
    assert r.metric == "notes.onset_f1" and math.isnan(r.current)


def test_improvement_is_not_regression() -> None:
    assert compare(report_with({"notes.onset_f1": 0.9}), {"notes.onset_f1": 0.8}) == []
