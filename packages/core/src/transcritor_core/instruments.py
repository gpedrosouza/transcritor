"""Orchestral instrument catalog.

Convention: sounding pitch = written pitch + ``transposition_semitones``.
``range_midi`` is the sounding range (inclusive MIDI note numbers).
"""

from dataclasses import dataclass
from typing import Literal

Family = Literal["woodwind", "brass", "strings", "keyboard", "plucked"]


@dataclass(frozen=True)
class Instrument:
    name: str
    family: Family
    transposition_semitones: int
    range_midi: tuple[int, int]
    clefs: tuple[str, ...]


_CATALOG: tuple[Instrument, ...] = (
    Instrument("flute", "woodwind", 0, (60, 96), ("treble",)),
    Instrument("piccolo", "woodwind", 12, (74, 108), ("treble",)),
    Instrument("oboe", "woodwind", 0, (58, 93), ("treble",)),
    Instrument("clarinet_bb", "woodwind", -2, (50, 94), ("treble",)),
    Instrument("bassoon", "woodwind", 0, (34, 75), ("bass", "tenor")),
    Instrument("horn_f", "brass", -7, (34, 77), ("treble", "bass")),
    Instrument("trumpet_bb", "brass", -2, (52, 82), ("treble",)),
    Instrument("trombone", "brass", 0, (40, 72), ("bass", "tenor")),
    Instrument("tuba", "brass", 0, (28, 65), ("bass",)),
    Instrument("violin", "strings", 0, (55, 103), ("treble",)),
    Instrument("viola", "strings", 0, (48, 91), ("alto", "treble")),
    Instrument("cello", "strings", 0, (36, 81), ("bass", "tenor", "treble")),
    Instrument("double_bass", "strings", -12, (28, 67), ("bass",)),
    Instrument("harp", "plucked", 0, (24, 103), ("treble", "bass")),
    Instrument("piano", "keyboard", 0, (21, 108), ("treble", "bass")),
)

_BY_NAME: dict[str, Instrument] = {i.name: i for i in _CATALOG}


def names() -> list[str]:
    """Return instrument names in catalog order."""
    return [i.name for i in _CATALOG]


def get(name: str) -> Instrument:
    """Return the instrument called ``name`` or raise ``KeyError`` listing valid names."""
    try:
        return _BY_NAME[name]
    except KeyError:
        raise KeyError(f"unknown instrument {name!r}; valid names: {', '.join(names())}") from None
