from fractions import Fraction

import pytest
from pydantic import BaseModel, ValidationError
from transcritor_core.rational import MusicalFraction


class M(BaseModel):
    x: MusicalFraction


def test_fraction_roundtrip_exact() -> None:
    assert M(x="1/3").x == Fraction(1, 3)
    assert M(x=Fraction(3, 8)).model_dump_json() == '{"x":"3/8"}'
    assert M.model_validate_json(M(x="1/3").model_dump_json()).x == Fraction(1, 3)


def test_fraction_accepts_int_and_integer_string() -> None:
    assert M(x="2").x == Fraction(2)
    assert M(x=2).x == Fraction(2)
    assert M(x=2).model_dump_json() == '{"x":"2"}'


@pytest.mark.parametrize("bad", [0.5, "1/0", "abc"])
def test_fraction_rejects(bad: object) -> None:
    with pytest.raises(ValidationError):
        M(x=bad)


def test_json_schema_is_string_pattern() -> None:
    schema = M.model_json_schema()["properties"]["x"]
    assert schema["type"] == "string"
    assert schema["pattern"] == r"^-?\d+(/\d+)?$"
