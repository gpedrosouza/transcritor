"""Oracle pipelines: a correct transcription must score 1.0 on every metric.

The oracle builds a ScoreDoc by hand from an item's references, following the Score IR
conventions (positional measures, whole-note beats, written spelling, true downbeats). It is
test-only and has no CI baseline.
"""

import json
import shutil
from collections.abc import Callable
from fractions import Fraction
from pathlib import Path
from typing import NamedTuple

import pytest
from music21 import meter, note, stream
from transcritor_core import (
    Hints,
    KeySegment,
    MeterSegment,
    NotatedElement,
    Notation,
    Note,
    Part,
    ProducedBy,
    ScoreDoc,
    Spelling,
    Timeline,
    Tonality,
    midi_to_hz,
)
from transcritor_eval.align import read_downbeats, reference_notes_from_score
from transcritor_eval.dataset import read_reference_notes, write_reference_notes
from transcritor_eval.pipelines import PIPELINES, Pipeline, null_pipeline
from transcritor_eval.runner import run_eval

DATASETS = Path(__file__).resolve().parents[1] / "datasets"
CI_DIR = DATASETS / "ci"
CI_REFS = CI_DIR / "refs"


class Written(NamedTuple):
    """One written note: positional measure, beat (whole-note fraction) and written pitch."""

    measure: int
    beat: Fraction
    spelling: Spelling


class Oracle(NamedTuple):
    notes_csv: Path
    downbeats_s: list[float]  # true downbeats only
    written: list[Written]  # one per reference note, in onset order
    meter: tuple[int, int, int]  # start_measure, numerator, denominator
    written_duration: Fraction


def oracle_pipeline(oracle: Oracle) -> Pipeline:
    def pipeline(audio_path: Path, hints: Hints) -> ScoreDoc:
        assert hints.key is None  # the oracle estimates the key itself
        doc = null_pipeline(audio_path, hints)
        producer = ProducedBy(adapter="oracle", version="0")
        refs = read_reference_notes(oracle.notes_csv)
        assert len(refs) == len(oracle.written)
        notes = [
            Note(
                id=f"n{i}",
                onset_s=r.onset_s,
                offset_s=r.offset_s,
                pitch_hz=midi_to_hz(r.pitch_midi),
                pitch_midi=float(r.pitch_midi),
                confidence=1.0,
                produced_by=producer,
            )
            for i, r in enumerate(refs)
        ]
        elements = [
            NotatedElement(
                id=f"e{i}",
                note_ids=[f"n{i}"],
                kind="note",
                part_id="p1",
                measure=w.measure,
                beat=w.beat,
                written_duration=oracle.written_duration,
                spelling=[w.spelling],
            )
            for i, w in enumerate(oracle.written)
        ]
        start, num, den = oracle.meter
        part = Part.from_instrument("p1", hints.instruments[0].instrument)
        return ScoreDoc.model_validate(
            doc.model_copy(
                update={
                    "parts": [part.model_copy(update={"notes": notes})],
                    "timeline": Timeline(
                        downbeats_s=oracle.downbeats_s,
                        meter_segments=[
                            MeterSegment(
                                start_measure=start,
                                numerator=num,
                                denominator=den,  # type: ignore[arg-type]
                                confidence=1.0,
                            )
                        ],
                    ),
                    "tonality": Tonality(
                        key_segments=[
                            KeySegment(
                                start_measure=start,
                                tonic_step="C",
                                tonic_alter=0,
                                mode="major",
                                confidence=1.0,
                            )
                        ]
                    ),
                    "notation": Notation(elements=elements),
                }
            ).model_dump()
        )

    return pipeline


@pytest.fixture
def use_oracle(monkeypatch: pytest.MonkeyPatch) -> Callable[[Oracle], str]:
    def install(oracle: Oracle) -> str:
        monkeypatch.setitem(PIPELINES, "oracle", oracle_pipeline(oracle))
        return "oracle"

    return install


def _spell(name: str) -> Spelling:
    return Spelling(step=name[0], alter=0, octave=int(name[1:]))  # type: ignore[arg-type]


def test_oracle_scores_one_on_the_ci_set(use_oracle: Callable[[Oracle], str]) -> None:
    scale = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]
    oracle = Oracle(
        notes_csv=CI_REFS / "c_major_scale_flute.notes.csv",
        downbeats_s=[0.0, 2.0],  # two 4/4 measures; the final 4.0 is the end, not a downbeat
        written=[Written(1 + i // 4, Fraction(i % 4, 4), _spell(n)) for i, n in enumerate(scale)],
        meter=(1, 4, 4),
        written_duration=Fraction(1, 4),
    )
    report = run_eval(CI_DIR / "manifest.json", "ci", use_oracle(oracle))
    assert [i.status for i in report.items] == ["ok"], report.items
    assert report.means and all(v == 1.0 for v in report.means.values()), report.means


@pytest.fixture
def pickup_manifest(tmp_path: Path) -> Path:
    """3/4 piece with a one-beat pickup (G4 | A4 B4 C5), 0.5 s per beat, plus its manifest."""
    pickup = stream.Measure(number=0)
    pickup.append([meter.TimeSignature("3/4"), note.Note("G4")])
    pickup.paddingLeft = 2.0
    full = stream.Measure(number=1)
    full.append([note.Note("A4"), note.Note("B4"), note.Note("C5")])
    part = stream.Part()
    part.append([pickup, full])
    refs = tmp_path / "refs"
    refs.mkdir()
    stream.Score([part]).write("musicxml", fp=str(refs / "pickup.musicxml"))
    (refs / "pickup.downbeats.txt").write_text("0.0\n0.5\n2.0\n", encoding="utf-8")
    notes = reference_notes_from_score(
        refs / "pickup.musicxml", read_downbeats(refs / "pickup.downbeats.txt")
    )
    write_reference_notes(notes, refs / "pickup.notes.csv")
    (tmp_path / "audio").mkdir()
    shutil.copy(CI_DIR / "audio" / "c_major_scale_flute.wav", tmp_path / "audio" / "pickup.wav")
    manifest = {
        "name": "pickup",
        "audio_root": "manifest",
        "items": [
            {
                "id": "pickup",
                "instrument": "flute",
                "audio": "audio/pickup.wav",
                "reference_notes": "refs/pickup.notes.csv",
                "reference_score": "refs/pickup.musicxml",
                "reference_downbeats": "refs/pickup.downbeats.txt",
                "key": {"tonic_step": "C", "tonic_alter": 0, "mode": "major"},
                "license": "CC0-1.0",
                "source": "test",
                "subsets": ["ci"],
            }
        ],
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def _pickup_oracle(manifest: Path, downbeats_s: list[float]) -> Oracle:
    written = [
        Written(0, Fraction(0), _spell("G4")),  # pickup: beat 0 is the start of its content
        Written(1, Fraction(0), _spell("A4")),
        Written(1, Fraction(1, 4), _spell("B4")),
        Written(1, Fraction(1, 2), _spell("C5")),
    ]
    return Oracle(
        notes_csv=manifest.parent / "refs" / "pickup.notes.csv",
        downbeats_s=downbeats_s,
        written=written,
        meter=(0, 3, 4),
        written_duration=Fraction(1, 4),
    )


def test_oracle_with_pickup_scores_one(
    pickup_manifest: Path, use_oracle: Callable[[Oracle], str]
) -> None:
    oracle = _pickup_oracle(pickup_manifest, downbeats_s=[0.5])  # only the real barline
    report = run_eval(pickup_manifest, "ci", use_oracle(oracle))
    assert [i.status for i in report.items] == ["ok"], report.items
    assert report.means["notes.downbeat_f1"] == 1.0
    assert report.means["notation.position_recall"] == 1.0
    assert all(v == 1.0 for v in report.means.values()), report.means


def test_fake_pickup_downbeat_is_penalized(
    pickup_manifest: Path, use_oracle: Callable[[Oracle], str]
) -> None:
    oracle = _pickup_oracle(pickup_manifest, downbeats_s=[0.0, 0.5])
    report = run_eval(pickup_manifest, "ci", use_oracle(oracle))
    assert report.means["notes.downbeat_f1"] < 1.0
