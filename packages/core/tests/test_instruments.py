import pytest
from transcritor_core.instruments import get, names


def test_transpositions() -> None:
    assert get("clarinet_bb").transposition_semitones == -2
    assert get("horn_f").transposition_semitones == -7
    assert get("piccolo").transposition_semitones == 12
    assert get("double_bass").transposition_semitones == -12


def test_ranges_valid() -> None:
    for n in names():
        lo, hi = get(n).range_midi
        assert 0 <= lo < hi <= 127


def test_unknown_lists_valid_names() -> None:
    with pytest.raises(KeyError, match="flute"):
        get("kazoo")


def test_names_in_catalog_order_and_consistent() -> None:
    listed = names()
    assert listed[0] == "flute"
    assert listed[-1] == "piano"
    assert len(listed) == 15
    assert all(get(n).name == n for n in listed)


def test_clefs_and_family() -> None:
    assert get("cello").clefs == ("bass", "tenor", "treble")
    assert get("harp").family == "plucked"
    assert get("piano").range_midi == (21, 108)
