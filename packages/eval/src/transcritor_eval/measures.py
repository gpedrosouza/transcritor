"""Positional measure indexing and true downbeats shared by alignment and metrics.

Measures are indexed BY POSITION, never by the MusicXML ``number`` attribute: the first
measure is the pickup (index 0) iff its content is shorter than a full bar of its time
signature; the remaining measures are 1..N in order.
"""

from fractions import Fraction
from pathlib import Path

from music21 import converter, stream

__all__ = ["has_pickup", "indexed_measures", "parse_score", "reference_downbeats"]


def parse_score(score_path: Path) -> stream.Score:
    score = converter.parse(str(score_path))
    if not isinstance(score, stream.Score):
        raise ValueError(f"{score_path} does not contain a single score")
    return score


def has_pickup(measures: list[stream.Measure]) -> bool:
    """True iff the first measure's content is shorter than its time signature's full bar."""
    if not measures:
        return False
    first = measures[0]
    content = Fraction(first.duration.quarterLength)
    return content < Fraction(first.barDuration.quarterLength)


def indexed_measures(part: stream.Part) -> list[tuple[int, stream.Measure]]:
    """The part's measures paired with their positional index (pickup = 0, then 1..N)."""
    measures = list(part.getElementsByClass(stream.Measure))
    start = 0 if has_pickup(measures) else 1
    return [(start + i, m) for i, m in enumerate(measures)]


def reference_downbeats(
    score_path: Path, downbeats_s: list[float], part_index: int = 0
) -> list[float]:
    """The true downbeats of a reference: barline times excluding the pickup start and end.

    ``downbeats_s`` is the annotated file's content: the start of each measure (pickup
    included) plus the end time of the last measure. The final end time is not a downbeat,
    and neither is the start of a pickup.
    """
    measures = list(parse_score(score_path).parts[part_index].getElementsByClass(stream.Measure))
    n = len(measures)
    if len(downbeats_s) != n + 1:
        raise ValueError(
            f"expected {n + 1} downbeats ({n} measures + end time), got {len(downbeats_s)}"
        )
    return downbeats_s[1:-1] if has_pickup(measures) else downbeats_s[:-1]
