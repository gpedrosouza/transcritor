"""Baseline comparison: the gate that blocks quality regressions (fails closed)."""

import math
from typing import NamedTuple

from transcritor_eval.report import EvalReport


class Regression(NamedTuple):
    metric: str
    baseline: float
    current: float  # nan when the metric is missing from the report


def compare(
    report: EvalReport, baseline: dict[str, float], tolerance: float = 0.01
) -> list[Regression]:
    """Return baseline metrics that dropped by more than ``tolerance``.

    A metric that is missing from the report, or NaN in it, counts as a regression.
    """
    regressions: list[Regression] = []
    for metric, base in baseline.items():
        current = report.means.get(metric, float("nan"))
        if math.isnan(current) or current < base - tolerance:
            regressions.append(Regression(metric, base, current))
    return regressions
