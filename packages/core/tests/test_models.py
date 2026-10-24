from datetime import UTC, datetime
from fractions import Fraction

import pytest
from pydantic import ValidationError
from transcritor_core.models import (
    SCHEMA_VERSION,
    AudioInfo,
    Hints,
    Op,
    OpKind,
    Part,
    ScoreDoc,
    Timeline,
)

NOW = datetime(2026, 10, 23, 12, 0, tzinfo=UTC)


def test_new_doc_defaults(make_source) -> None:
    doc = ScoreDoc.new(source=make_source())
    assert doc.schema_version == SCHEMA_VERSION == "1.0.0"
    assert len(doc.id) == 32
    assert doc.parts == [] and doc.notation.elements == []
    assert doc.source.hints == Hints()


def test_defaults_are_not_shared(make_source) -> None:
    a = ScoreDoc.new(source=make_source())
    b = ScoreDoc.new(source=make_source())
    a.timeline.beats_s.append(1.0)
    assert b.timeline.beats_s == []
    assert a.id != b.id


def test_part_from_catalog() -> None:
    p = Part.from_instrument("p1", "clarinet_bb")
    assert p.transposition_semitones == -2 and p.range_midi == (50, 94)


def test_unknown_instrument_rejected() -> None:
    with pytest.raises(ValidationError, match="kazoo"):
        Part(id="p", instrument="kazoo", transposition_semitones=0, range_midi=(0, 1))


def test_note_offset_after_onset(make_note) -> None:
    with pytest.raises(ValidationError):
        make_note(onset_s=1.0, offset_s=1.0)


@pytest.mark.parametrize(
    "overrides",
    [
        {"onset_s": -0.1},
        {"pitch_hz": 0.0},
        {"velocity": 128},
        {"confidence": 1.1},
    ],
)
def test_note_bounds(overrides: dict[str, object], make_note) -> None:
    with pytest.raises(ValidationError):
        make_note(**overrides)


def test_duplicate_note_ids_rejected(make_note, make_doc) -> None:
    doc = make_doc()
    doc.parts[0].notes[1] = make_note(id="n1", onset_s=0.5, offset_s=1.0)
    with pytest.raises(ValidationError, match="n1"):
        ScoreDoc.model_validate(doc.model_dump(mode="json"))


def test_element_with_unknown_note_id_rejected(make_element, make_doc) -> None:
    data = make_doc().model_dump(mode="json")
    data["notation"]["elements"] = [make_element(note_ids=["ghost"]).model_dump(mode="json")]
    with pytest.raises(ValidationError, match="ghost"):
        ScoreDoc.model_validate(data)


def test_element_with_unknown_part_rejected(make_element, make_doc) -> None:
    data = make_doc().model_dump(mode="json")
    data["notation"]["elements"] = [make_element(part_id="nope").model_dump(mode="json")]
    with pytest.raises(ValidationError, match="nope"):
        ScoreDoc.model_validate(data)


def test_valid_doc_roundtrip(make_element, make_doc) -> None:
    doc = make_doc()
    data = make_doc().model_dump(mode="json")
    data["notation"]["elements"] = [make_element().model_dump(mode="json")]
    again = ScoreDoc.model_validate(data)
    assert again.notation.elements[0].beat == Fraction(0)
    assert again.notation.elements[0].written_duration == Fraction(1, 4)
    assert again.model_dump(mode="json") == data
    assert doc.parts[0].notes[0].id == "n1"


def test_extra_field_rejected(make_doc) -> None:
    with pytest.raises(ValidationError):
        ScoreDoc.model_validate({**make_doc().model_dump(mode="json"), "foo": 1})


def test_bad_sha256_rejected() -> None:
    with pytest.raises(ValidationError):
        AudioInfo(sha256="xyz", duration_s=1.0, sample_rate=44100, channels=1, original_name="a")


def test_op_uses_from_alias() -> None:
    op = Op(
        id="o1",
        created_at=NOW,
        author="u",
        layer="listen",
        target_id="n1",
        op=OpKind.set_pitch,
        **{"from": 66},
        to=67,
    )
    assert op.model_dump(mode="json", by_alias=True)["from"] == 66
    assert Op.model_validate(op.model_dump(mode="json", by_alias=True)) == op


def test_op_serializes_by_alias_by_default() -> None:
    op = Op(
        id="o1",
        created_at=NOW,
        author="u",
        layer="listen",
        target_id=None,
        op=OpKind.insert_note,
        from_=None,
        to={"pitch": 67},
    )
    dumped = op.model_dump(mode="json")
    assert "from" in dumped and "from_" not in dumped
    assert Op.model_validate_json(op.model_dump_json()) == op


# --- contract invariants ---


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_note_rejects_non_finite_times(bad: float, make_note) -> None:
    with pytest.raises(ValidationError):
        make_note(offset_s=bad)


def test_timeline_rejects_nan() -> None:
    with pytest.raises(ValidationError):
        Timeline(downbeats_s=[0.0, float("nan")])


def test_op_rejects_nan() -> None:
    with pytest.raises(ValidationError):
        Op(
            id="o1",
            created_at=NOW,
            author="u",
            layer="listen",
            target_id="n1",
            op=OpKind.set_pitch,
            from_=66,
            to=float("nan"),
        )


@pytest.mark.parametrize("duration", ["0", "-1/4"])
def test_written_duration_must_be_positive(duration: str, make_element) -> None:
    with pytest.raises(ValidationError, match="greater than 0"):
        make_element(written_duration=duration)


def test_beat_must_not_be_negative(make_element) -> None:
    with pytest.raises(ValidationError, match="greater than or equal to 0"):
        make_element(beat="-1/8")


@pytest.mark.parametrize("pickup", ["0", "-1/4"])
def test_pickup_beats_must_be_positive(pickup: str) -> None:
    with pytest.raises(ValidationError, match="greater than 0"):
        Hints(pickup_beats=pickup)


def test_pickup_beats_accepts_whole_note_fraction() -> None:
    assert Hints(pickup_beats="1/4").pickup_beats == Fraction(1, 4)


def test_duplicate_part_ids_rejected(make_doc) -> None:
    data = make_doc().model_dump(mode="json")
    extra = Part.from_instrument("p1", "violin").model_dump(mode="json")
    data["parts"].append(extra)
    with pytest.raises(ValidationError, match="duplicate part id 'p1'"):
        ScoreDoc.model_validate(data)


def test_duplicate_element_ids_rejected(make_element, make_doc) -> None:
    data = make_doc().model_dump(mode="json")
    data["notation"]["elements"] = [
        make_element(id="e1", note_ids=["n1"]).model_dump(mode="json"),
        make_element(id="e1", note_ids=["n2"], beat="1/4").model_dump(mode="json"),
    ]
    with pytest.raises(ValidationError, match="duplicate element id 'e1'"):
        ScoreDoc.model_validate(data)


@pytest.mark.parametrize("version", ["1.0", "v1.0.0", "1.0.0-beta", ""])
def test_schema_version_must_be_semver(version: str, make_doc) -> None:
    data = {**make_doc().model_dump(mode="json"), "schema_version": version}
    with pytest.raises(ValidationError):
        ScoreDoc.model_validate(data)
