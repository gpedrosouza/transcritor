from transcritor_core import (
    AudioInfo,
    Note,
    Part,
    ProducedBy,
    ScoreDoc,
    Source,
    Timeline,
    midi_to_hz,
)
from transcritor_eval.dataset import RefNote
from transcritor_eval.metrics_notes import NoteMetrics, downbeat_f1, note_metrics

REF = [RefNote(0.0, 0.5, 60), RefNote(1.0, 1.5, 62), RefNote(2.0, 2.5, 64)]
DB = [0.0, 2.0, 4.0]  # reference downbeats + final instant


def _source() -> Source:
    audio = AudioInfo(
        sha256="0" * 64, duration_s=4.0, sample_rate=44100, channels=1, original_name="x.wav"
    )
    return Source(audio=audio)


def empty_doc() -> ScoreDoc:
    return ScoreDoc.new(source=_source())


def doc_from_ref(
    ref: list[RefNote],
    downbeats: list[float] | None = None,
    onset_shift: float = 0.0,
    pitch_shift: int = 0,
) -> ScoreDoc:
    producer = ProducedBy(adapter="test", version="0")
    notes = [
        Note(
            id=f"n{i}",
            onset_s=n.onset_s + onset_shift,
            offset_s=n.offset_s + onset_shift,
            pitch_hz=midi_to_hz(n.pitch_midi + pitch_shift),
            pitch_midi=float(n.pitch_midi + pitch_shift),
            confidence=1.0,
            produced_by=producer,
        )
        for i, n in enumerate(ref)
    ]
    part = Part.from_instrument("p1", "flute").model_copy(update={"notes": notes})
    return empty_doc().model_copy(
        update={"parts": [part], "timeline": Timeline(downbeats_s=downbeats or [])}
    )


def test_perfect_match() -> None:
    m = note_metrics(REF, DB, doc_from_ref(REF, downbeats=[0.0, 2.0]))
    assert m.onset_f1 == 1.0 and m.offset_f1 == 1.0 and m.downbeat_f1 == 1.0


def test_onset_within_50ms_counts() -> None:
    assert note_metrics(REF, DB, doc_from_ref(REF, onset_shift=0.04)).onset_f1 == 1.0


def test_wrong_pitch_misses() -> None:
    assert note_metrics(REF, DB, doc_from_ref(REF, pitch_shift=1)).onset_f1 == 0.0


def test_final_time_is_not_a_downbeat() -> None:
    assert downbeat_f1(DB, [0.0, 2.0]) == 1.0


def test_empty_doc_is_zero() -> None:
    m = note_metrics(REF, DB, empty_doc())
    assert m.model_dump() == dict.fromkeys(NoteMetrics.model_fields, 0.0)


def test_empty_reference_is_zero() -> None:
    m = note_metrics([], [], doc_from_ref(REF, downbeats=[0.0]))
    assert m.model_dump() == dict.fromkeys(NoteMetrics.model_fields, 0.0)
