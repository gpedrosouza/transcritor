from pathlib import Path

import pytest
from transcritor_core.licenses import (
    ALLOWED_LICENSES,
    evaluate,
    is_allowed,
    workspace_package_names,
)


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


def _pkg(name: str, license_name: str = "MIT") -> dict[str, str]:
    return {"Name": name, "Version": "1.0", "License": license_name}


def test_workspace_package_names_normalized(tmp_path: Path) -> None:
    for folder, name in [("core", "transcritor-core"), ("eval", "Transcritor_Eval")]:
        (tmp_path / "packages" / folder).mkdir(parents=True)
        (tmp_path / "packages" / folder / "pyproject.toml").write_text(
            f'[project]\nname = "{name}"\nversion = "0"\n', encoding="utf-8"
        )
    assert workspace_package_names(tmp_path) == {"transcritor-core", "transcritor-eval"}


def test_workspace_member_skipped_but_lookalike_checked() -> None:
    skip = {"transcritor-core"}
    packages = [
        _pkg("transcritor_core", "GPL-3.0"),
        _pkg("transcritor-evil", "GPL-3.0"),
        _pkg("numpy"),
    ]
    checked, rejected = evaluate(packages, skip)
    assert checked == 2
    assert rejected == ["transcritor-evil 1.0: GPL-3.0"]


def test_empty_input_checks_nothing() -> None:
    assert evaluate([], set()) == (0, [])
    assert evaluate([_pkg("transcritor-core")], {"transcritor-core"}) == (0, [])


def test_script_fails_on_empty_run(monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib.util
    import subprocess

    path = Path(__file__).resolve().parents[3] / "scripts" / "check_licenses.py"
    spec = importlib.util.spec_from_file_location("check_licenses", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a, 0, stdout="[]", stderr=""),
    )
    assert module.main() == 1
