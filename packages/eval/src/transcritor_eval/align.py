"""Timed reference notes from a MusicXML score plus annotated measure downbeats."""

from bisect import bisect_right
from fractions import Fraction
from pathlib import Path

from music21 import stream

from transcritor_eval.dataset import RefNote, write_reference_notes
from transcritor_eval.measures import indexed_measures, parse_score

__all__ = ["read_downbeats", "reference_notes_from_score", "write_reference_notes"]


def read_downbeats(path: Path) -> list[float]:
    """Read one time per line, or Audacity labels (tab-separated, first column)."""
    times: list[float] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        t = float(line.split("\t")[0])
        if times and t <= times[-1]:
            raise ValueError(f"downbeats must be strictly increasing (line {line_no})")
        times.append(t)
    return times


def reference_notes_from_score(
    score_path: Path, downbeats_s: list[float], part_index: int = 0
) -> list[RefNote]:
    """Time every sounding note of a part by linear interpolation inside each measure.

    `downbeats_s` holds the start of each measure (pickup included) plus the end time of the last.
    """
    part = parse_score(score_path).parts[part_index].toSoundingPitch(inPlace=False)
    # Measure lengths come from the unstripped part: stripTies stretches a measure whose
    # last note is tied into the next one.
    measures = indexed_measures(part)
    n = len(measures)
    if len(downbeats_s) != n + 1:
        raise ValueError(
            f"expected {n + 1} downbeats ({n} measures + end time), got {len(downbeats_s)}"
        )

    # Exact quarter-length arithmetic, so tuplets never overshoot a barline through rounding.
    starts = [Fraction(0)]
    for index, measure in measures:
        length = Fraction(measure.duration.quarterLength)
        if length <= 0:
            raise ValueError(f"measure {index} (by position) is empty (zero duration)")
        starts.append(starts[-1] + length)

    def time_at(q: Fraction) -> float:
        if q >= starts[-1]:
            if q > starts[-1]:
                raise ValueError(f"offset {q} lies past the end of the score")
            return downbeats_s[-1]
        i = bisect_right(starts, q) - 1
        frac = float((q - starts[i]) / (starts[i + 1] - starts[i]))
        return downbeats_s[i] + frac * (downbeats_s[i + 1] - downbeats_s[i])

    notes: list[RefNote] = []
    stripped = part.stripTies(inPlace=False).getElementsByClass(stream.Measure)
    for i, measure in enumerate(stripped):
        for element in measure.recurse().notes:
            if element.duration.isGrace:
                continue
            onset_q = starts[i] + Fraction(element.getOffsetInHierarchy(measure))
            offset_q = onset_q + Fraction(element.duration.quarterLength)
            onset_s, offset_s = time_at(onset_q), time_at(offset_q)
            notes += [RefNote(onset_s, offset_s, int(p.midi)) for p in element.pitches]
    return sorted(notes, key=lambda note: (note.onset_s, note.pitch_midi))
