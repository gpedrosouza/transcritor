import pytest
from transcritor_core.licenses import ALLOWED_LICENSES, is_allowed


@pytest.mark.parametrize(
    "expr",
    [
        "MIT",
        "BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0",
        "Apache-2.0 OR BSD-2-Clause",
        "Apache Software License; BSD License",
        "  MIT  ;  BSD License ",
        "Mozilla Public License 2.0 (MPL 2.0)",
    ],
)
def test_allowed(expr: str) -> None:
    assert is_allowed(expr)


@pytest.mark.parametrize(
    "expr",
    ["GPL-3.0", "AGPL-3.0", "CC-BY-NC-4.0", "UNKNOWN", "", "   ", "MIT AND GPL-3.0", "mit", "MIT;"],
)
def test_rejected(expr: str) -> None:
    assert not is_allowed(expr)


def test_allowlist_contains_policy_entries() -> None:
    assert "MPL-2.0" in ALLOWED_LICENSES
    assert "GPL-3.0" not in ALLOWED_LICENSES
