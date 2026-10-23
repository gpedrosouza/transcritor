import pytest
from transcritor_core.errors import SchemaVersionError, TranscritorError
from transcritor_core.units import hz_to_midi, midi_to_hz


def test_a4() -> None:
    assert hz_to_midi(440.0) == 69.0
    assert midi_to_hz(60) == pytest.approx(261.6256, abs=1e-4)
    assert hz_to_midi(midi_to_hz(61.5)) == pytest.approx(61.5)


def test_hz_to_midi_rejects_non_positive() -> None:
    with pytest.raises(ValueError):
        hz_to_midi(0.0)


def test_schema_version_error_keeps_found() -> None:
    err = SchemaVersionError("unsupported schema", found="0.9.0")
    assert isinstance(err, TranscritorError)
    assert err.found == "0.9.0"
    assert str(err) == "unsupported schema"
