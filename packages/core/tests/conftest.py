from collections.abc import Callable

import pytest
from transcritor_core.models import (
    AudioInfo,
    NotatedElement,
    Note,
    Part,
    ProducedBy,
    ScoreDoc,
    Source,
    Spelling,
    Tuplet,
)

# Shared factories are exposed as fixtures: with --import-mode=importlib a conftest
# cannot be imported by name, so tests receive the factories as arguments.


@pytest.fixture
def make_source() -> Callable[[], Source]:
    def factory() -> Source:
        return Source(
            audio=AudioInfo(
                sha256="a" * 64,
                duration_s=10.0,
                sample_rate=44100,
                channels=1,
                original_name="take.wav",
            )
        )

    return factory


@pytest.fixture
def make_note() -> Callable[..., Note]:
    def factory(**overrides: object) -> Note:
        data: dict[str, object] = {
            "id": "n1",
            "onset_s": 0.0,
            "offset_s": 0.5,
            "pitch_hz": 440.0,
            "pitch_midi": 69.0,
            "confidence": 0.9,
            "produced_by": ProducedBy(adapter="stub", version="0"),
        }
        data.update(overrides)
        return Note.model_validate(data)

    return factory


@pytest.fixture
def make_element() -> Callable[..., NotatedElement]:
    def factory(**overrides: object) -> NotatedElement:
        data: dict[str, object] = {
            "id": "e1",
            "note_ids": ["n1"],
            "kind": "note",
            "part_id": "p1",
            "measure": 1,
            "beat": "0",
            "written_duration": "1/4",
            "spelling": [Spelling(step="A", alter=0, octave=4)],
        }
        data.update(overrides)
        return NotatedElement.model_validate(data)

    return factory


@pytest.fixture
def make_doc(
    make_source: Callable[[], Source], make_note: Callable[..., Note]
) -> Callable[[], ScoreDoc]:
    def factory() -> ScoreDoc:
        part = Part.from_instrument("p1", "flute")
        part.notes = [make_note(id="n1"), make_note(id="n2", onset_s=0.5, offset_s=1.0)]
        return ScoreDoc.new(source=make_source()).model_copy(update={"parts": [part]})

    return factory


@pytest.fixture
def make_doc_with_notation(
    make_doc: Callable[[], ScoreDoc], make_element: Callable[..., NotatedElement]
) -> Callable[[], ScoreDoc]:
    """Document with a triplet-eighth at beat 1/3 (tuplet) alongside a plain element."""

    def factory() -> ScoreDoc:
        doc = make_doc()
        doc.notation.elements = [
            make_element(id="e1", note_ids=["n1"]),
            make_element(
                id="e2",
                note_ids=["n2"],
                beat="1/3",
                written_duration="1/12",
                tuplet=Tuplet(actual=3, normal=2),
            ),
        ]
        return doc

    return factory
