import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from transcritor_eval.cli import main
from transcritor_eval.dataset import read_reference_notes
from transcritor_eval.report import EvalReport, ItemResult, to_json

PKG = Path(__file__).resolve().parents[1]
CI_DIR = PKG / "datasets" / "ci"
CI_MANIFEST = CI_DIR / "manifest.json"
CI_BASELINE = PKG / "baselines" / "ci.json"


def write_report(path: Path, means: dict[str, float], statuses: tuple[str, ...] = ("ok",)) -> Path:
    items = [
        ItemResult(item_id=f"i{n}", status=s, message="boom" if s != "ok" else "")  # type: ignore[arg-type]
        for n, s in enumerate(statuses)
    ]
    report = EvalReport(
        dataset="d",
        subset="ci",
        pipeline="null",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        items=items,
        means=means,
    )
    to_json(report, path)
    return path


def test_cli_run_and_gate(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "nested" / "out"
    assert (
        main(
            [
                *("run", "--manifest", str(CI_MANIFEST), "--subset", "ci", "--pipeline", "null"),
                "--out",
                str(out),
            ]
        )
        == 0
    )
    assert (out / "report.md").exists()
    assert "1 ok, 0 skipped, 0 error" in capsys.readouterr().out
    assert main(["gate", "--report", str(out / "report.json"), "--baseline", str(CI_BASELINE)]) == 0
    assert "OK: no regressions" in capsys.readouterr().out


def test_gate_prints_regression(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    report = write_report(tmp_path / "r.json", {"a": 0.5, "b": 0.0})
    # to_json writes NaN as null (unloadable, exit 2); hand-write a literal NaN to test the gate.
    report.write_text(report.read_text(encoding="utf-8").replace('"b": 0.0', '"b": NaN'))
    base = tmp_path / "b.json"
    base.write_text(json.dumps({"a": 0.9, "b": 0.1, "c": 0.2}), encoding="utf-8")
    assert main(["gate", "--report", str(report), "--baseline", str(base)]) == 1
    out = capsys.readouterr().out
    assert "REGRESSION a: baseline 0.900 -> current 0.500" in out
    assert "REGRESSION b: baseline 0.100 -> current nan" in out
    assert "REGRESSION c: baseline 0.200 -> current nan" in out


def test_gate_fails_on_error_item(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    report = write_report(tmp_path / "r.json", {"a": 1.0}, ("ok", "error"))
    base = tmp_path / "b.json"
    base.write_text(json.dumps({"a": 0.5}), encoding="utf-8")
    assert main(["gate", "--report", str(report), "--baseline", str(base)]) == 1
    assert "i1" in capsys.readouterr().out


def test_baseline_writes_sorted_means(tmp_path: Path) -> None:
    report = write_report(tmp_path / "r.json", {"b": 0.5, "a": 0.25})
    out = tmp_path / "base.json"
    assert main(["baseline", "--report", str(report), "--out", str(out)]) == 0
    assert out.read_text(encoding="utf-8") == '{\n  "a": 0.25,\n  "b": 0.5\n}\n'


def test_baseline_refuses_empty_means(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    report = write_report(tmp_path / "r.json", {})
    out = tmp_path / "base.json"
    assert main(["baseline", "--report", str(report), "--out", str(out)]) == 1
    assert not out.exists()
    assert capsys.readouterr().err


@pytest.mark.parametrize("bad", ["error", "skipped"])
def test_baseline_refuses_bad_items(tmp_path: Path, bad: str) -> None:
    report = write_report(tmp_path / "r.json", {"a": 1.0}, ("ok", bad))
    out = tmp_path / "base.json"
    assert main(["baseline", "--report", str(report), "--out", str(out)]) == 1
    assert not out.exists()


def test_missing_and_bad_files_exit_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    base = tmp_path / "b.json"
    base.write_text('{"a": 0.5}', encoding="utf-8")
    assert main(["gate", "--report", str(tmp_path / "nope.json"), "--baseline", str(base)]) == 2
    assert capsys.readouterr().err
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    assert main(["gate", "--report", str(bad), "--baseline", str(base)]) == 2
    good = write_report(tmp_path / "r.json", {"a": 1.0})
    assert main(["gate", "--report", str(good), "--baseline", str(bad)]) == 2


def test_align_reproduces_committed_csv(tmp_path: Path) -> None:
    out = tmp_path / "notes.csv"
    code = main(
        [
            "align",
            str(CI_DIR / "refs" / "c_major_scale_flute.musicxml"),
            str(CI_DIR / "refs" / "c_major_scale_flute.downbeats.txt"),
            "--out",
            str(out),
        ]
    )
    assert code == 0
    committed = CI_DIR / "refs" / "c_major_scale_flute.notes.csv"
    assert read_reference_notes(out) == read_reference_notes(committed)


def test_report_with_null_mean_exits_2(tmp_path: Path) -> None:
    report = write_report(tmp_path / "r.json", {"a": float("nan")})
    base = tmp_path / "b.json"
    base.write_text(json.dumps({"a": 0.5}), encoding="utf-8")
    assert main(["gate", "--report", str(report), "--baseline", str(base)]) == 2


def test_baseline_with_nan_exits_2(tmp_path: Path) -> None:
    report = write_report(tmp_path / "r.json", {"a": 1.0})
    base = tmp_path / "b.json"
    base.write_text('{"a": NaN}', encoding="utf-8")
    assert main(["gate", "--report", str(report), "--baseline", str(base)]) == 2


def test_empty_baseline_exits_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    report = write_report(tmp_path / "r.json", {"a": 1.0})
    base = tmp_path / "b.json"
    base.write_text("{}", encoding="utf-8")
    assert main(["gate", "--report", str(report), "--baseline", str(base)]) == 2
    assert "empty" in capsys.readouterr().err


@pytest.mark.parametrize("tol", ["nan", "inf", "-0.5"])
def test_invalid_tolerance_exits_2(tmp_path: Path, tol: str) -> None:
    report = write_report(tmp_path / "r.json", {"a": 0.0})
    base = tmp_path / "b.json"
    base.write_text('{"a": 0.9}', encoding="utf-8")
    argv = ["gate", "--report", str(report), "--baseline", str(base), f"--tolerance={tol}"]
    assert main(argv) == 2
