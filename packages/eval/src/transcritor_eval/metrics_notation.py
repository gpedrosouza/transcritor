"""Notation, key and meter metrics comparing a ScoreDoc's notation layer to a MusicXML reference."""

from fractions import Fraction
from pathlib import Path
from typing import NamedTuple

import mir_eval
from music21 import chord, meter, note, stream, tie
from pydantic import BaseModel, ConfigDict
from transcritor_core import KeyHint, KeySegment, NotatedElement, ScoreDoc, Spelling

from transcritor_eval.align import _parse_score

__all__ = [
    "NotationMetrics",
    "RefElement",
    "notation_metrics",
    "reference_elements",
    "reference_meters",
]

_STEP_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
# Names accepted by mir_eval.key, one per pitch class, for keys it cannot spell (E#, Cb, ##, bb).
_PC_NAME = ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")
_MIR_EVAL_TONICS = frozenset(mir_eval.key.KEY_TO_SEMITONE)


class RefElement(NamedTuple):
    measure: int
    beat: Fraction
    written_duration: Fraction
    spelling: tuple[Spelling, ...]
    accidental_shown: bool


class NotationMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    position_precision: float
    position_recall: float
    duration_accuracy: float
    spelling_accuracy: float
    accidental_accuracy: float
    key_score: float
    meter_accuracy: float


def _spelling_key(s: Spelling) -> tuple[int, int]:
    """Sort by MIDI number, then by step so enharmonic pairs in a chord order deterministically."""
    return 12 * (s.octave + 1) + _STEP_PC[s.step] + s.alter, "CDEFGAB".index(s.step)


def _sorted_spelling(spelling: list[Spelling] | tuple[Spelling, ...]) -> tuple[Spelling, ...]:
    return tuple(sorted(spelling, key=_spelling_key))


def _is_tie_continuation(element: note.NotRest) -> bool:
    """True for a note (or chord whose every note) continues or ends a tie."""

    def continues(t: tie.Tie | None) -> bool:
        return t is not None and t.type in ("continue", "stop")

    if continues(element.tie):
        return True
    if isinstance(element, chord.Chord):
        return all(continues(n.tie) for n in element.notes)
    return False


def reference_elements(score_path: Path, part_index: int = 0) -> list[RefElement]:
    """Written notes and chords of a part, one element per written tie segment.

    Mirrors the Score IR, where a tie's continuation is its own `kind: tie` element: ties are
    not merged, each segment keeps its own written duration, and segments that continue or end
    a tie are excluded (as are rests and grace notes). `beat` is the music21 offset inside the
    measure (a pickup's first note is at 0); `beat` and `written_duration` are whole-note
    fractions. Pitches are written, not sounding. `accidental_shown` is True iff some pitch's
    accidental has `displayStatus is True` as parsed.
    """
    part = _parse_score(score_path).parts[part_index]
    elements: list[RefElement] = []
    for measure in part.getElementsByClass(stream.Measure):
        for element in measure.recurse().notes:
            if element.duration.isGrace or _is_tie_continuation(element):
                continue
            spelling = [
                Spelling(
                    step=p.step,
                    alter=int(p.accidental.alter) if p.accidental is not None else 0,
                    octave=p.octave,
                )
                for p in element.pitches
            ]
            shown = any(
                p.accidental is not None and p.accidental.displayStatus is True
                for p in element.pitches
            )
            elements.append(
                RefElement(
                    measure=int(measure.number),
                    beat=Fraction(element.getOffsetInHierarchy(measure)) / 4,
                    written_duration=Fraction(element.duration.quarterLength) / 4,
                    spelling=_sorted_spelling(spelling),
                    accidental_shown=shown,
                )
            )
    return elements


def reference_meters(score_path: Path) -> dict[int, tuple[int, int]]:
    """Time signature in force at each measure of the first part (pickup included).

    A pickup gets its notated time signature, not its actual (shorter) length.
    """
    part = _parse_score(score_path).parts[0]
    meters: dict[int, tuple[int, int]] = {}
    for measure in part.getElementsByClass(stream.Measure):
        # measure.timeSignature first: getContextByClass can return the previous measure's one.
        ts = measure.timeSignature or measure.getContextByClass(meter.TimeSignature)
        if ts is None:
            raise ValueError(f"measure {measure.number} of {score_path} has no time signature")
        meters[int(measure.number)] = (int(ts.numerator), int(ts.denominator))
    return meters


def _key_name(step: str, alter: int, mode: str) -> str:
    """mir_eval key name, e.g. "F# minor"; unsupported spellings map to an enharmonic name."""
    tonic = step + ("#" * alter if alter > 0 else "b" * -alter)
    if tonic.lower() not in _MIR_EVAL_TONICS:
        tonic = _PC_NAME[(_STEP_PC[step] + alter) % 12]
    return f"{tonic} {mode}"


def _key_score(reference: KeyHint | None, segments: list[KeySegment]) -> float:
    if reference is None or not segments:
        return 0.0
    est = segments[0]
    return float(
        mir_eval.key.weighted_score(
            _key_name(reference.tonic_step, reference.tonic_alter, reference.mode),
            _key_name(est.tonic_step, est.tonic_alter, est.mode),
        )
    )


def _meter_accuracy(reference: dict[int, tuple[int, int]], doc: ScoreDoc) -> float:
    segments = doc.timeline.meter_segments
    if not reference or not segments:
        return 0.0
    hits = 0
    for measure, expected in reference.items():
        in_force = [s for s in segments if s.start_measure <= measure]
        if in_force:
            seg = max(in_force, key=lambda s: s.start_measure)
            hits += (seg.numerator, seg.denominator) == expected
    return hits / len(reference)


def notation_metrics(
    score_path: Path, reference_key: KeyHint | None, doc: ScoreDoc
) -> NotationMetrics:
    """Match reference and document elements by exact (measure, beat), then score what matched.

    Only `note`/`chord` elements of the document's first part are evaluated. Each reference
    element takes the first unused document element at its position, in document order; any
    other document element counts against precision.
    """
    refs = reference_elements(score_path)
    estimates: list[NotatedElement] = []
    if doc.parts:
        part_id = doc.parts[0].id
        estimates = [
            e for e in doc.notation.elements if e.kind in ("note", "chord") and e.part_id == part_id
        ]

    by_position: dict[tuple[int, Fraction], list[NotatedElement]] = {}
    for est in estimates:
        by_position.setdefault((est.measure, est.beat), []).append(est)
    pairs: list[tuple[RefElement, NotatedElement]] = []
    for ref in refs:
        candidates = by_position.get((ref.measure, ref.beat))
        if candidates:
            pairs.append((ref, candidates.pop(0)))

    def accuracy(hits: int) -> float:
        return hits / len(pairs) if pairs else 0.0

    return NotationMetrics(
        position_precision=len(pairs) / len(estimates) if estimates else 0.0,
        position_recall=len(pairs) / len(refs) if refs else 0.0,
        duration_accuracy=accuracy(sum(r.written_duration == e.written_duration for r, e in pairs)),
        spelling_accuracy=accuracy(
            sum(r.spelling == _sorted_spelling(e.spelling) for r, e in pairs)
        ),
        accidental_accuracy=accuracy(
            sum(r.accidental_shown == e.accidental_shown for r, e in pairs)
        ),
        key_score=_key_score(reference_key, doc.tonality.key_segments),
        meter_accuracy=_meter_accuracy(reference_meters(score_path), doc),
    )
