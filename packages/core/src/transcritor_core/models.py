"""Score IR: the single data contract between all Transcritor modules.

See docs/arquitetura/score-ir.md. Breaking changes require a ``SCHEMA_VERSION`` bump.
"""

from datetime import datetime
from enum import StrEnum
from fractions import Fraction
from typing import Annotated, Final, Literal, Self
from uuid import uuid4

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    WithJsonSchema,
    model_validator,
)

from transcritor_core import instruments
from transcritor_core.rational import MusicalFraction

SCHEMA_VERSION: Final = "1.0.0"

Step = Literal["C", "D", "E", "F", "G", "A", "B"]
Mode = Literal["major", "minor"]
Denominator = Literal[1, 2, 4, 8, 16, 32]


def _positive(value: Fraction) -> Fraction:
    if value <= 0:
        raise ValueError("must be greater than 0")
    return value


def _non_negative(value: Fraction) -> Fraction:
    if value < 0:
        raise ValueError("must be greater than or equal to 0")
    return value


# The JSON Schema can only exclude the sign; zero is rejected at validation time.
_UNSIGNED_FRACTION_SCHEMA = WithJsonSchema({"type": "string", "pattern": r"^\d+(/\d+)?$"})
PositiveFraction = Annotated[MusicalFraction, AfterValidator(_positive), _UNSIGNED_FRACTION_SCHEMA]
NonNegativeFraction = Annotated[
    MusicalFraction, AfterValidator(_non_negative), _UNSIGNED_FRACTION_SCHEMA
]


def _check_unique(kind: str, ids: list[str]) -> None:
    seen: set[str] = set()
    for item_id in ids:
        if item_id in seen:
            raise ValueError(f"duplicate {kind} id {item_id!r}")
        seen.add(item_id)


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class ProducedBy(_Model):
    adapter: str
    version: str


class Note(_Model):
    """A detected note (listen layer)."""

    id: str
    onset_s: float = Field(ge=0)
    offset_s: float
    pitch_hz: float = Field(gt=0, description="Sounding pitch.")
    pitch_midi: float = Field(
        description="Sounding pitch as a MIDI number; may be fractional before rounding."
    )
    velocity: int | None = Field(default=None, ge=0, le=127)
    confidence: float = Field(ge=0, le=1)
    produced_by: ProducedBy

    @model_validator(mode="after")
    def _offset_after_onset(self) -> Self:
        if self.offset_s <= self.onset_s:
            raise ValueError(f"note {self.id!r}: offset_s must be greater than onset_s")
        return self


class Part(_Model):
    """One instrument line. Sounding pitch = written pitch + transposition_semitones."""

    id: str
    instrument: str
    transposition_semitones: int
    range_midi: tuple[int, int]
    notes: list[Note] = Field(default_factory=list)

    @model_validator(mode="after")
    def _instrument_in_catalog(self) -> Self:
        try:
            instruments.get(self.instrument)
        except KeyError as exc:
            raise ValueError(str(exc.args[0])) from None
        return self

    @classmethod
    def from_instrument(cls, part_id: str, instrument: str) -> Self:
        """Build an empty part, filling transposition and range from the catalog."""
        inst = instruments.get(instrument)
        return cls(
            id=part_id,
            instrument=instrument,
            transposition_semitones=inst.transposition_semitones,
            range_midi=inst.range_midi,
        )


class Spelling(_Model):
    step: Step
    alter: int = Field(ge=-2, le=2)
    octave: int


class KeyHint(_Model):
    tonic_step: Step
    tonic_alter: int = Field(ge=-2, le=2)
    mode: Mode


class MeterHint(_Model):
    numerator: int = Field(ge=1)
    denominator: Denominator


class InstrumentCount(_Model):
    instrument: str
    count: int = Field(ge=1)


class RegionHint(_Model):
    start_s: float
    end_s: float
    key: KeyHint | None = None
    meter: MeterHint | None = None
    bpm: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _end_after_start(self) -> Self:
        if self.end_s <= self.start_s:
            raise ValueError("region: end_s must be greater than start_s")
        return self


class Hints(_Model):
    """User-provided hints; they take precedence over inference."""

    instruments: list[InstrumentCount] = Field(default_factory=list)
    key: KeyHint | None = None
    meter: MeterHint | None = None
    bpm: float | None = Field(default=None, gt=0)
    pickup_beats: PositiveFraction | None = Field(
        default=None,
        description=(
            "Pickup (anacrusis) length in fractions of a whole note, the same unit as "
            "NotatedElement.beat (e.g. '1/4' = one quarter note)."
        ),
    )
    regions: list[RegionHint] = Field(default_factory=list)


class AudioInfo(_Model):
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    duration_s: float = Field(gt=0)
    sample_rate: int = Field(gt=0)
    channels: int = Field(ge=1)
    original_name: str


class Source(_Model):
    audio: AudioInfo
    hints: Hints = Field(default_factory=Hints)


class TempoPoint(_Model):
    time_s: float = Field(ge=0)
    bpm: float = Field(gt=0)


class MeterSegment(_Model):
    start_measure: int = Field(ge=0)
    numerator: int = Field(ge=1)
    denominator: Denominator
    confidence: float = Field(ge=0, le=1)
    from_hint: bool = False


class Timeline(_Model):
    beats_s: list[float] = Field(default_factory=list)
    downbeats_s: list[float] = Field(default_factory=list)
    tempo_curve: list[TempoPoint] = Field(default_factory=list)
    meter_segments: list[MeterSegment] = Field(default_factory=list)


class KeySegment(_Model):
    start_measure: int = Field(ge=0)
    tonic_step: Step
    tonic_alter: int = Field(ge=-2, le=2)
    mode: Mode
    confidence: float = Field(ge=0, le=1)
    from_hint: bool = False


class Tonality(_Model):
    key_segments: list[KeySegment] = Field(default_factory=list)


class Tuplet(_Model):
    actual: int = Field(ge=2)
    normal: int = Field(ge=1)


class Decision(_Model):
    rule: str
    reason: str


class NotatedElement(_Model):
    """One written element of the score (notate layer)."""

    id: str
    note_ids: list[str] = Field(description="Listen-layer notes that originated this element.")
    kind: Literal["note", "chord", "rest", "tie"]
    part_id: str
    staff: int = Field(default=1, ge=1)
    voice: int = Field(default=1, ge=1)
    measure: int = Field(
        ge=0, description="Measures are numbered from 1; the pickup (anacrusis) is measure 0."
    )
    beat: NonNegativeFraction = Field(
        description="Offset from the start of the measure, in fractions of a whole note."
    )
    written_duration: PositiveFraction = Field(description="Fraction of a whole note.")
    tuplet: Tuplet | None = None
    spelling: list[Spelling] = Field(
        default_factory=list, description="Written (not sounding) pitch of each note."
    )
    accidental_shown: bool = False
    decision: Decision | None = None


class Notation(_Model):
    elements: list[NotatedElement] = Field(default_factory=list)


class WarningCode(StrEnum):
    LOW_CONFIDENCE_NOTE = "LOW_CONFIDENCE_NOTE"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    AMBIGUOUS_METER = "AMBIGUOUS_METER"
    KEY_CHANGE_SUSPECTED = "KEY_CHANGE_SUSPECTED"
    UNQUANTIZABLE_RHYTHM = "UNQUANTIZABLE_RHYTHM"
    SIMPLIFIED = "SIMPLIFIED"


class Location(_Model):
    part_id: str | None = None
    note_id: str | None = None
    measure: int | None = None


class DocWarning(_Model):
    code: WarningCode
    severity: Literal["info", "warning"]
    location: Location
    message: str


class ProvenanceEntry(_Model):
    stage: str
    module_version: str
    adapter: str | None = None
    params: dict[str, JsonValue] = Field(default_factory=dict)
    started_at: datetime
    duration_ms: float = Field(ge=0)


class ScoreDoc(_Model):
    schema_version: str = Field(default=SCHEMA_VERSION, pattern=r"^\d+\.\d+\.\d+$")
    id: str
    source: Source
    parts: list[Part] = Field(default_factory=list)
    timeline: Timeline = Field(default_factory=Timeline)
    tonality: Tonality = Field(default_factory=Tonality)
    notation: Notation = Field(default_factory=Notation)
    warnings: list[DocWarning] = Field(default_factory=list)
    provenance: list[ProvenanceEntry] = Field(default_factory=list)

    @classmethod
    def new(cls, source: Source) -> Self:
        """Create an empty document with a fresh id."""
        return cls(id=uuid4().hex, source=source)

    @model_validator(mode="after")
    def _references_are_consistent(self) -> Self:
        _check_unique("part", [p.id for p in self.parts])
        _check_unique("note", [n.id for p in self.parts for n in p.notes])
        _check_unique("element", [e.id for e in self.notation.elements])
        part_ids = {p.id for p in self.parts}
        note_ids = {n.id for p in self.parts for n in p.notes}
        for el in self.notation.elements:
            if el.part_id not in part_ids:
                raise ValueError(f"element {el.id!r} references unknown part {el.part_id!r}")
            for nid in el.note_ids:
                if nid not in note_ids:
                    raise ValueError(f"element {el.id!r} references unknown note {nid!r}")
        return self


OpLayer = Literal["listen", "notation", "timeline", "tonality"]


class OpKind(StrEnum):
    set_pitch = "set_pitch"
    set_onset = "set_onset"
    set_offset = "set_offset"
    insert_note = "insert_note"
    delete_note = "delete_note"
    set_spelling = "set_spelling"
    set_duration = "set_duration"
    set_voice = "set_voice"
    set_meter = "set_meter"
    set_key = "set_key"
    move_barline = "move_barline"


class Op(BaseModel):
    """An edit operation sent by the editor; ``from``/``to`` are the values before/after."""

    model_config = ConfigDict(
        extra="forbid", allow_inf_nan=False, populate_by_name=True, serialize_by_alias=True
    )

    id: str
    created_at: datetime
    author: str
    layer: OpLayer
    target_id: str | None = Field(description="Affected element id; null for insertions.")
    op: OpKind
    from_: JsonValue = Field(alias="from")
    to: JsonValue
