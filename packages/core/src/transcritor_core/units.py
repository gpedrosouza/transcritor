"""Pitch unit conversions (A4 = 440 Hz = MIDI 69)."""

import math

_A4_HZ = 440.0
_A4_MIDI = 69.0


def hz_to_midi(hz: float) -> float:
    """Convert a frequency in Hz to a (fractional) MIDI note number."""
    if hz <= 0:
        raise ValueError(f"frequency must be positive, got {hz}")
    return _A4_MIDI + 12.0 * math.log2(hz / _A4_HZ)


def midi_to_hz(midi: float) -> float:
    """Convert a (fractional) MIDI note number to a frequency in Hz."""
    return _A4_HZ * math.pow(2.0, (midi - _A4_MIDI) / 12.0)
