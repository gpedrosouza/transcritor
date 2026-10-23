from pathlib import Path

import pytest
from music21 import chord, instrument, meter, note, stream, tie
from transcritor_eval import align
from transcritor_eval.align import (
    read_downbeats,
    reference_notes_from_score,
    write_reference_notes,
)
from transcritor_eval.dataset import RefNote, read_reference_notes

CI_REFS = Path(__file__).resolve().parents[1] / "datasets" / "ci" / "refs"


def _write(part: stream.Part, path: Path) -> Path:
    stream.Score([part]).write("musicxml", fp=str(path))
    return path


def _part(time_signature: str, elements: list[note.GeneralNote]) -> stream.Part:
    part = stream.Part()
    part.append(meter.TimeSignature(time_signature))
    for element in elements:
        part.append(element)
    part.makeMeasures(inPlace=True)
    return part


def _tied(pitch: int, kind: str) -> note.Note:
    n = note.Note(pitch)
    n.tie = tie.Tie(kind)
    return n


@pytest.fixture
def score_4_4_two_bars(tmp_path: Path) -> Path:
    pitches = [60, 62, 64, 65, 67, 69, 71, 72]
    return _write(_part("4/4", [note.Note(p) for p in pitches]), tmp_path / "two_bars.musicxml")


@pytest.fixture
def score_with_pickup(tmp_path: Path) -> Path:
    pickup = stream.Measure(number=0)
    pickup.append(meter.TimeSignature("3/4"))
    pickup.append(note.Note(67))
    pickup.paddingLeft = 2.0
    full = stream.Measure(number=1)
    for p in (60, 62, 64):
        full.append(note.Note(p))
    part = stream.Part()
    part.append([pickup, full])
    return _write(part, tmp_path / "pickup.musicxml")


@pytest.fixture
def score_tied_over_bar(tmp_path: Path) -> Path:
    # bar 1: C D E F(tied) | bar 2: F(tied) G A B
    elements: list[note.GeneralNote] = [note.Note(60), note.Note(62), note.Note(64)]
    elements += [_tied(65, "start"), _tied(65, "stop"), note.Note(67), note.Note(69)]
    elements += [note.Note(71)]
    return _write(_part("4/4", elements), tmp_path / "tied.musicxml")


@pytest.fixture
def score_clarinet_d(tmp_path: Path) -> Path:
    part = stream.Part()
    part.insert(0, instrument.Clarinet())
    part.append(meter.TimeSignature("4/4"))
    part.append(note.Note("D4", quarterLength=4.0))
    part.makeMeasures(inPlace=True)
    return _write(part, tmp_path / "clarinet.musicxml")


def test_two_bars_quarters(score_4_4_two_bars: Path) -> None:
    notes = reference_notes_from_score(score_4_4_two_bars, [0.0, 2.0, 4.0])
    assert [n.onset_s for n in notes] == pytest.approx([0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5])
    assert [n.offset_s for n in notes] == pytest.approx([0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4])
    assert [n.pitch_midi for n in notes] == [60, 62, 64, 65, 67, 69, 71, 72]


def test_uneven_downbeats_interpolate_per_measure(score_4_4_two_bars: Path) -> None:
    notes = reference_notes_from_score(score_4_4_two_bars, [1.0, 3.0, 7.0])
    assert [n.onset_s for n in notes] == pytest.approx([1, 1.5, 2, 2.5, 3, 4, 5, 6])
    assert notes[-1].offset_s == pytest.approx(7.0)


def test_pickup_measure(score_with_pickup: Path) -> None:
    # anacruse de 1 semínima em 3/4, depois 1 compasso cheio
    notes = reference_notes_from_score(score_with_pickup, [0.0, 0.5, 2.0])
    assert notes[0].onset_s == pytest.approx(0.0)
    assert notes[0].offset_s == pytest.approx(0.5)
    assert notes[1].onset_s == pytest.approx(0.5)
    assert [n.onset_s for n in notes[1:]] == pytest.approx([0.5, 1.0, 1.5])


def test_tie_across_barline_is_one_note(score_tied_over_bar: Path) -> None:
    notes = reference_notes_from_score(score_tied_over_bar, [0.0, 2.0, 4.0])
    assert len(notes) == 7
    tied = next(n for n in notes if n.onset_s == pytest.approx(1.5))
    assert tied.pitch_midi == 65
    assert tied.offset_s == pytest.approx(2.5)


def test_tie_end_uses_the_measure_where_it_falls(score_tied_over_bar: Path) -> None:
    # bar 2 is twice as slow as bar 1: the tied note ends 1 beat into bar 2
    notes = reference_notes_from_score(score_tied_over_bar, [0.0, 2.0, 6.0])
    tied = next(n for n in notes if n.pitch_midi == 65)
    assert (tied.onset_s, tied.offset_s) == pytest.approx((1.5, 3.0))


def test_chords_rests_and_grace_notes(tmp_path: Path) -> None:
    grace = note.Note(74).getGrace()
    elements: list[note.GeneralNote] = [chord.Chord([64, 60]), note.Rest(), grace, note.Note(72)]
    elements += [note.Rest()]
    path = _write(_part("4/4", elements), tmp_path / "chords.musicxml")
    notes = reference_notes_from_score(path, [0.0, 2.0])
    assert notes == [
        RefNote(0.0, 0.5, 60),
        RefNote(0.0, 0.5, 64),
        RefNote(1.0, 1.5, 72),
    ]


def test_triplets_end_exactly_on_the_final_downbeat(tmp_path: Path) -> None:
    elements: list[note.GeneralNote] = [note.Note(60, quarterLength=1 / 3) for _ in range(12)]
    path = _write(_part("4/4", elements), tmp_path / "triplets.musicxml")
    notes = reference_notes_from_score(path, [0.0, 2.0])
    assert len(notes) == 12
    assert notes[-1].offset_s == 2.0
    assert notes[3].onset_s == pytest.approx(0.5)


def test_part_index_selects_part(tmp_path: Path) -> None:
    upper = _part("4/4", [note.Note(72, quarterLength=4.0)])
    lower = _part("4/4", [note.Note(48, quarterLength=4.0)])
    path = tmp_path / "two_parts.musicxml"
    stream.Score([upper, lower]).write("musicxml", fp=str(path))
    assert [n.pitch_midi for n in reference_notes_from_score(path, [0.0, 2.0], 1)] == [48]


def test_downbeat_count_mismatch(score_4_4_two_bars: Path) -> None:
    with pytest.raises(ValueError, match=r"expected 3 downbeats"):
        reference_notes_from_score(score_4_4_two_bars, [0.0, 2.0])


def test_downbeat_count_mismatch_message(score_4_4_two_bars: Path) -> None:
    with pytest.raises(ValueError) as excinfo:
        reference_notes_from_score(score_4_4_two_bars, [0.0, 2.0, 4.0, 6.0])
    assert str(excinfo.value) == "expected 3 downbeats (2 measures + end time), got 4"


def test_empty_measure_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # music21's MusicXML reader fills empty measures with a rest, so build the score in memory
    first = stream.Measure(number=1)
    first.append(meter.TimeSignature("4/4"))
    first.append(note.Note(60, quarterLength=4.0))
    part = stream.Part()
    part.append([first, stream.Measure(number=2)])
    monkeypatch.setattr(align.converter, "parse", lambda _path: stream.Score([part]))
    with pytest.raises(ValueError, match=r"measure 2"):
        reference_notes_from_score(tmp_path / "unused.musicxml", [0.0, 2.0, 4.0])


def test_transposing_part_uses_sounding_pitch(score_clarinet_d: Path) -> None:
    # clarinete em Si♭: Ré escrito (62) soa Dó (60)
    assert reference_notes_from_score(score_clarinet_d, [0.0, 2.0])[0].pitch_midi == 60


def test_ci_reference_is_reproduced(tmp_path: Path) -> None:
    downbeats = read_downbeats(CI_REFS / "c_major_scale_flute.downbeats.txt")
    assert downbeats == [0.0, 2.0, 4.0]
    notes = reference_notes_from_score(CI_REFS / "c_major_scale_flute.musicxml", downbeats)
    out = tmp_path / "notes.csv"
    write_reference_notes(notes, out)
    expected = CI_REFS / "c_major_scale_flute.notes.csv"
    assert out.read_text(encoding="utf-8") == expected.read_text(encoding="utf-8")


def test_write_then_read_round_trip(tmp_path: Path) -> None:
    notes = [RefNote(0.0, 0.25, 60), RefNote(0.125, 1.5, 67)]
    path = tmp_path / "notes.csv"
    write_reference_notes(notes, path)
    assert read_reference_notes(path) == notes


def test_read_plain_downbeats(tmp_path: Path) -> None:
    path = tmp_path / "downbeats.txt"
    path.write_text("0.0\n\n1.5\n  3.25  \n\n", encoding="utf-8")
    assert read_downbeats(path) == [0.0, 1.5, 3.25]


def test_read_audacity_labels(tmp_path: Path) -> None:
    path = tmp_path / "labels.txt"
    path.write_text(
        "0.512000\t0.512000\t1\n2.480000\t2.480000\t2\n\n4.500000\t4.500000\tend\n",
        encoding="utf-8",
    )
    assert read_downbeats(path) == [0.512, 2.48, 4.5]


def test_read_downbeats_requires_strictly_increasing(tmp_path: Path) -> None:
    path = tmp_path / "downbeats.txt"
    path.write_text("0.0\n\n2.0\n2.0\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"line 4"):
        read_downbeats(path)
