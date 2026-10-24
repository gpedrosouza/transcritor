from fractions import Fraction
from pathlib import Path

import pytest
from music21 import chord, key, meter, note, stream, tie
from transcritor_core import (
    AudioInfo,
    KeyHint,
    KeySegment,
    MeterSegment,
    NotatedElement,
    Notation,
    Note,
    Part,
    ProducedBy,
    ScoreDoc,
    Source,
    Spelling,
    Timeline,
    Tonality,
    midi_to_hz,
)
from transcritor_eval.metrics_notation import (
    NotationMetrics,
    RefElement,
    notation_metrics,
    reference_elements,
    reference_meters,
)
from transcritor_eval.metrics_notation import _key_name as key_name

CI_SCORE = Path(__file__).parents[1] / "datasets" / "ci" / "refs" / "c_major_scale_flute.musicxml"
C_MAJOR = KeyHint(tonic_step="C", tonic_alter=0, mode="major")
G_MAJOR = KeyHint(tonic_step="G", tonic_alter=0, mode="major")
_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def _write(tmp_path: Path, name: str, measures: list[stream.Measure]) -> Path:
    score, part = stream.Score(), stream.Part()
    part.append(measures)
    score.append(part)
    path = tmp_path / name
    score.write("musicxml", fp=str(path))
    return path


@pytest.fixture
def score(tmp_path: Path) -> Path:
    """C major, 4/4: C D E F | G (half) G (half)."""
    m1 = stream.Measure(number=1)
    m1.append([meter.TimeSignature("4/4"), key.KeySignature(0)])
    m1.append([note.Note(p) for p in ("C4", "D4", "E4", "F4")])
    m2 = stream.Measure(number=2)
    m2.append([note.Note("G4", quarterLength=2), note.Note("G4", quarterLength=2)])
    return _write(tmp_path, "c.musicxml", [m1, m2])


@pytest.fixture
def score_with_f_sharp(tmp_path: Path) -> Path:
    """G major, 4/4: G F# F(natural) F# | chord C4-Eb4 (whole)."""
    m1 = stream.Measure(number=1)
    m1.append([meter.TimeSignature("4/4"), key.KeySignature(1)])
    m1.append([note.Note(p) for p in ("G4", "F#4", "F4", "F#4")])
    m2 = stream.Measure(number=2)
    m2.append(chord.Chord(["E-4", "C4"], quarterLength=4))
    return _write(tmp_path, "g.musicxml", [m1, m2])


@pytest.fixture
def score_with_pickup(tmp_path: Path) -> Path:
    """Quarter-note pickup in 3/4, one 3/4 measure, then a 2/4 measure; C5 tied over the bar."""
    m0 = stream.Measure(number=0)
    m0.append([meter.TimeSignature("3/4"), note.Note("G4")])
    m0.paddingLeft = 2.0
    m1 = stream.Measure(number=1)
    tied = note.Note("C5", quarterLength=2)
    tied.tie = tie.Tie("start")
    m1.append([note.Note("A4"), tied])
    m2 = stream.Measure(number=2)
    end = note.Note("C5", quarterLength=1)
    end.tie = tie.Tie("stop")
    m2.append([meter.TimeSignature("2/4"), end, note.Note("D5")])
    return _write(tmp_path, "pickup.musicxml", [m0, m1, m2])


def _source() -> Source:
    audio = AudioInfo(
        sha256="0" * 64, duration_s=4.0, sample_rate=44100, channels=1, original_name="x.wav"
    )
    return Source(audio=audio)


def empty_doc() -> ScoreDoc:
    return ScoreDoc.new(source=_source())


def _midi(s: Spelling) -> int:
    return 12 * (s.octave + 1) + _PC[s.step] + s.alter


def _respell(s: Spelling, respell: dict[str, str]) -> Spelling:
    name = s.step + ("#" * s.alter if s.alter > 0 else "b" * -s.alter)
    if name not in respell:
        return s
    target = respell[name]
    alter = target.count("#") - target.count("b")
    return Spelling(step=target[0], alter=alter, octave=s.octave)  # type: ignore[arg-type]


def doc_from_reference(
    score_path: Path,
    key_hint: KeyHint = C_MAJOR,
    respell: dict[str, str] | None = None,
) -> ScoreDoc:
    """Copy the reference notation, key and meters into a ScoreDoc (one part)."""
    producer = ProducedBy(adapter="test", version="0")
    notes: list[Note] = []
    elements: list[NotatedElement] = []
    for i, ref in enumerate(reference_elements(score_path)):
        ids = []
        for s in ref.spelling:
            nid = f"n{len(notes)}"
            midi = _midi(s)
            notes.append(
                Note(
                    id=nid,
                    onset_s=float(i),
                    offset_s=float(i) + 0.5,
                    pitch_hz=midi_to_hz(midi),
                    pitch_midi=float(midi),
                    confidence=1.0,
                    produced_by=producer,
                )
            )
            ids.append(nid)
        elements.append(
            NotatedElement(
                id=f"e{i}",
                note_ids=ids,
                kind="chord" if len(ref.spelling) > 1 else "note",
                part_id="p1",
                measure=ref.measure,
                beat=ref.beat,
                written_duration=ref.written_duration,
                spelling=[_respell(s, respell or {}) for s in ref.spelling],
                accidental_shown=ref.accidental_shown,
            )
        )
    segments: list[MeterSegment] = []
    for measure, (num, den) in sorted(reference_meters(score_path).items()):
        if not segments or (segments[-1].numerator, segments[-1].denominator) != (num, den):
            segments.append(
                MeterSegment(start_measure=measure, numerator=num, denominator=den, confidence=1)  # type: ignore[arg-type]
            )
    part = Part.from_instrument("p1", "flute").model_copy(update={"notes": notes})
    return ScoreDoc(
        id="d",
        source=_source(),
        parts=[part],
        timeline=Timeline(meter_segments=segments),
        tonality=Tonality(key_segments=[_key_segment(key_hint)]),
        notation=Notation(elements=elements),
    )


def _key_segment(k: KeyHint) -> KeySegment:
    return KeySegment(
        start_measure=1,
        tonic_step=k.tonic_step,
        tonic_alter=k.tonic_alter,
        mode=k.mode,
        confidence=1,
    )


def doc_with_key(step: str, alter: int, mode: str) -> ScoreDoc:
    k = KeyHint(tonic_step=step, tonic_alter=alter, mode=mode)  # type: ignore[arg-type]
    return empty_doc().model_copy(update={"tonality": Tonality(key_segments=[_key_segment(k)])})


def _with_elements(doc: ScoreDoc, elements: list[NotatedElement]) -> ScoreDoc:
    return doc.model_copy(update={"notation": Notation(elements=elements)})


# --- brief tests ---


def test_perfect_notation(score: Path) -> None:
    doc = doc_from_reference(score)
    m = notation_metrics(score, C_MAJOR, doc)
    assert (m.position_recall, m.spelling_accuracy, m.key_score, m.meter_accuracy) == (1, 1, 1, 1)


def test_enharmonic_spelling_counts_as_error(score_with_f_sharp: Path) -> None:
    doc = doc_from_reference(score_with_f_sharp, G_MAJOR, respell={"F#": "Gb"})
    assert notation_metrics(score_with_f_sharp, G_MAJOR, doc).spelling_accuracy < 1


def test_dominant_key_scores_half(score: Path) -> None:
    assert notation_metrics(score, C_MAJOR, doc_with_key("G", 0, "major")).key_score == 0.5


def test_empty_doc_scores_zero(score: Path) -> None:
    m = notation_metrics(score, C_MAJOR, empty_doc())
    assert m.position_recall == 0 and m.key_score == 0 and m.meter_accuracy == 0


# --- reference extraction ---


def test_reference_elements_written_spelling_and_accidentals(score_with_f_sharp: Path) -> None:
    refs = reference_elements(score_with_f_sharp)
    g, f_sharp, f_natural, f_sharp_again, ch = refs
    assert g == RefElement(
        1, Fraction(0), Fraction(1, 4), (Spelling(step="G", alter=0, octave=4),), False
    )
    assert f_sharp.spelling == (Spelling(step="F", alter=1, octave=4),)
    assert not f_sharp.accidental_shown  # covered by the key signature
    assert (
        f_natural.spelling == (Spelling(step="F", alter=0, octave=4),)
        and f_natural.accidental_shown
    )
    assert f_sharp_again.accidental_shown  # restored after the natural
    assert ch.measure == 2 and ch.written_duration == Fraction(1)
    assert ch.spelling == (
        Spelling(step="C", alter=0, octave=4),
        Spelling(step="E", alter=-1, octave=4),
    )  # sorted by MIDI
    assert ch.accidental_shown


def test_reference_pickup_ties_and_meters(score_with_pickup: Path) -> None:
    refs = reference_elements(score_with_pickup)
    assert [(r.measure, r.beat, r.written_duration) for r in refs] == [
        (0, Fraction(0), Fraction(1, 4)),
        (1, Fraction(0), Fraction(1, 4)),
        (1, Fraction(1, 4), Fraction(1, 2)),  # tie-start segment, its own written length
        (2, Fraction(1, 4), Fraction(1, 4)),  # no element for the tie continuation at (2, 0)
    ]
    assert reference_meters(score_with_pickup) == {0: (3, 4), 1: (3, 4), 2: (2, 4)}


def test_tied_note_written_as_tie_segments_scores_perfectly(score_with_pickup: Path) -> None:
    doc = doc_from_reference(score_with_pickup)  # G4 | A4 C5(half, tie start) | D5
    half = doc.notation.elements[2]
    continuation = half.model_copy(
        update={
            "id": "t",
            "kind": "tie",
            "measure": 2,
            "beat": Fraction(0),
            "written_duration": Fraction(1, 4),
        }
    )
    elements = [*doc.notation.elements[:3], continuation, doc.notation.elements[3]]
    m = notation_metrics(score_with_pickup, None, _with_elements(doc, elements))
    assert (m.position_precision, m.position_recall, m.duration_accuracy) == (1, 1, 1)


def test_tied_chord_continuation_is_excluded(tmp_path: Path) -> None:
    m1 = stream.Measure(number=1)
    start = chord.Chord(["C4", "E4"], quarterLength=4)
    for n in start.notes:
        n.tie = tie.Tie("start")
    m1.append([meter.TimeSignature("4/4"), start])
    m2 = stream.Measure(number=2)
    stop = chord.Chord(["C4", "E4"], quarterLength=2)
    for n in stop.notes:
        n.tie = tie.Tie("stop")
    m2.append([stop, note.Note("G4", quarterLength=2)])
    refs = reference_elements(_write(tmp_path, "chords.musicxml", [m1, m2]))
    assert [(r.measure, r.beat, r.written_duration) for r in refs] == [
        (1, Fraction(0), Fraction(1)),
        (2, Fraction(1, 2), Fraction(1, 2)),
    ]


def test_ci_score() -> None:
    refs = reference_elements(CI_SCORE)
    assert len(refs) == 8 and {r.measure for r in refs} == {1, 2}
    assert all(r.written_duration == Fraction(1, 4) for r in refs)
    assert reference_meters(CI_SCORE) == {1: (4, 4), 2: (4, 4)}
    m = notation_metrics(CI_SCORE, C_MAJOR, doc_from_reference(CI_SCORE))
    assert m == NotationMetrics(
        position_precision=1.0,
        position_recall=1.0,
        duration_accuracy=1.0,
        spelling_accuracy=1.0,
        accidental_accuracy=1.0,
        key_score=1.0,
        meter_accuracy=1.0,
    )


# --- matching and accuracies ---


def test_extra_element_at_same_position_lowers_precision_only(score: Path) -> None:
    doc = doc_from_reference(score)
    elements = list(doc.notation.elements)
    wrong = elements[0].model_copy(
        update={"id": "extra", "spelling": [Spelling(step="B", alter=0, octave=3)]}
    )
    m = notation_metrics(score, C_MAJOR, _with_elements(doc, [elements[0], wrong, *elements[1:]]))
    assert m.position_recall == 1.0
    assert m.position_precision == pytest.approx(6 / 7)
    assert m.spelling_accuracy == 1.0  # the first element in document order is the match


def test_shifted_beat_is_unmatched_and_durations_compared(score: Path) -> None:
    doc = doc_from_reference(score)
    elements = list(doc.notation.elements)
    elements[0] = elements[0].model_copy(update={"beat": Fraction(1, 8)})
    elements[1] = elements[1].model_copy(update={"written_duration": Fraction(1, 8)})
    elements[2] = elements[2].model_copy(update={"accidental_shown": True})
    m = notation_metrics(score, C_MAJOR, _with_elements(doc, elements))
    assert m.position_recall == pytest.approx(5 / 6) and m.position_precision == pytest.approx(
        5 / 6
    )
    assert m.duration_accuracy == pytest.approx(4 / 5)
    assert m.accidental_accuracy == pytest.approx(4 / 5)


def test_rests_and_other_parts_are_ignored(score: Path) -> None:
    doc = doc_from_reference(score)
    rest = NotatedElement(
        id="r",
        note_ids=[],
        kind="rest",
        part_id="p1",
        measure=1,
        beat=Fraction(1, 8),
        written_duration=Fraction(1, 8),
    )
    other = Part.from_instrument("p2", "flute")
    stray = rest.model_copy(update={"id": "s", "kind": "note", "part_id": "p2"})
    doc = doc.model_copy(
        update={
            "parts": [*doc.parts, other],
            "notation": Notation(elements=[*doc.notation.elements, rest, stray]),
        }
    )
    assert notation_metrics(score, C_MAJOR, doc).position_precision == 1.0


def test_chord_spelling_order_does_not_matter(score_with_f_sharp: Path) -> None:
    doc = doc_from_reference(score_with_f_sharp, G_MAJOR)
    elements = list(doc.notation.elements)
    elements[-1] = elements[-1].model_copy(update={"spelling": elements[-1].spelling[::-1]})
    m = notation_metrics(score_with_f_sharp, G_MAJOR, _with_elements(doc, elements))
    assert m.spelling_accuracy == 1.0


def test_enharmonic_respelling_is_one_error_per_element(score_with_f_sharp: Path) -> None:
    doc = doc_from_reference(score_with_f_sharp, G_MAJOR, respell={"F#": "Gb"})
    assert notation_metrics(score_with_f_sharp, G_MAJOR, doc).spelling_accuracy == pytest.approx(
        3 / 5
    )


# --- key ---


def test_missing_reference_key_scores_zero(score: Path) -> None:
    assert notation_metrics(score, None, doc_from_reference(score)).key_score == 0.0


@pytest.mark.parametrize(
    ("step", "alter", "mode", "expected"),
    [
        ("F", 1, "minor", "F# minor"),
        ("B", -1, "major", "Bb major"),
        ("C", 0, "major", "C major"),
        ("C", -1, "major", "B major"),
        ("E", 1, "minor", "F minor"),
        ("C", 2, "major", "D major"),
        ("E", -2, "minor", "D minor"),
        ("F", 2, "major", "G major"),
    ],
)
def test_key_name(step: str, alter: int, mode: str, expected: str) -> None:
    assert key_name(step, alter, mode) == expected


def test_double_sharp_key_is_scored_enharmonically(score: Path) -> None:
    doc = doc_with_key("C", 2, "major")  # C## == D
    d_major = KeyHint(tonic_step="D", tonic_alter=0, mode="major")
    assert notation_metrics(score, d_major, doc).key_score == 1.0


# --- meter ---


def test_meter_uses_segment_in_force_including_pickup(score_with_pickup: Path) -> None:
    def with_meters(*segments: tuple[int, int, int]) -> ScoreDoc:
        meters = [
            MeterSegment(start_measure=s, numerator=n, denominator=d, confidence=1)  # type: ignore[arg-type]
            for s, n, d in segments
        ]
        return empty_doc().model_copy(update={"timeline": Timeline(meter_segments=meters)})

    def acc(doc: ScoreDoc) -> float:
        return notation_metrics(score_with_pickup, None, doc).meter_accuracy

    assert acc(with_meters((0, 3, 4), (2, 2, 4))) == 1.0
    assert acc(with_meters((0, 3, 4))) == pytest.approx(2 / 3)
    assert acc(with_meters((1, 3, 4), (2, 2, 4))) == pytest.approx(2 / 3)  # pickup has none
    assert acc(with_meters((0, 1, 4), (1, 3, 4), (2, 2, 4))) == pytest.approx(2 / 3)
