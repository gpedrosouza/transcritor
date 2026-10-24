from pathlib import Path

import pytest
from music21 import meter, note, stream
from transcritor_eval.measures import indexed_measures, parse_score, reference_downbeats
from transcritor_eval.metrics_notes import downbeat_f1


def _score(tmp_path: Path, numbers: tuple[int, int], pickup: bool, implicit: bool = False) -> Path:
    """Two 3/4 measures with the given MusicXML numbers; the first is a 1-beat pickup if asked."""
    first = stream.Measure(number=numbers[0])
    first.append(meter.TimeSignature("3/4"))
    if pickup:
        first.append(note.Note("G4"))
        first.paddingLeft = 2.0
    else:
        first.append([note.Note("G4"), note.Note("A4"), note.Note("B4")])
    second = stream.Measure(number=numbers[1])
    second.append([note.Note("C5"), note.Note("D5"), note.Note("E5")])
    part = stream.Part()
    part.append([first, second])
    path = tmp_path / f"m{numbers[0]}_{numbers[1]}_{pickup}.musicxml"
    stream.Score([part]).write("musicxml", fp=str(path))
    if implicit:
        text = path.read_text(encoding="utf-8")
        text = text.replace(
            f'implicit="no" number="{numbers[0]}"', f'implicit="yes" number="{numbers[0]}"', 1
        )
        path.write_text(text, encoding="utf-8")
    return path


def _indices(path: Path) -> list[int]:
    return [i for i, _ in indexed_measures(parse_score(path).parts[0])]


@pytest.mark.parametrize(
    ("numbers", "pickup", "implicit", "expected"),
    [
        ((1, 2), False, False, [1, 2]),
        ((37, 38), False, False, [1, 2]),  # excerpt: MusicXML numbers are ignored
        ((1, 1), False, False, [1, 2]),  # duplicate numbers
        ((0, 1), True, False, [0, 1]),
        ((1, 2), True, True, [0, 1]),  # pickup exported as number "1" + implicit
    ],
)
def test_measures_are_indexed_by_position(
    tmp_path: Path, numbers: tuple[int, int], pickup: bool, implicit: bool, expected: list[int]
) -> None:
    assert _indices(_score(tmp_path, numbers, pickup, implicit)) == expected


def test_reference_downbeats_drop_end_time(tmp_path: Path) -> None:
    path = _score(tmp_path, (1, 2), pickup=False)
    assert reference_downbeats(path, [0.0, 1.5, 3.0]) == [0.0, 1.5]


def test_reference_downbeats_drop_pickup_start(tmp_path: Path) -> None:
    path = _score(tmp_path, (0, 1), pickup=True)
    assert reference_downbeats(path, [0.0, 0.5, 2.0]) == [0.5]


def test_reference_downbeats_count_mismatch(tmp_path: Path) -> None:
    path = _score(tmp_path, (1, 2), pickup=False)
    with pytest.raises(ValueError, match=r"expected 3 downbeats"):
        reference_downbeats(path, [0.0, 1.5])


def test_pickup_start_is_not_a_downbeat(tmp_path: Path) -> None:
    ref = reference_downbeats(_score(tmp_path, (0, 1), pickup=True), [0.0, 0.5, 2.0])
    assert downbeat_f1(ref, [0.5]) == 1.0  # correct estimate: only the barline
    assert downbeat_f1(ref, [0.0, 0.5]) < 1.0  # fake downbeat at the pickup start
