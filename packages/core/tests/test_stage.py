from collections.abc import Callable, Mapping
from datetime import UTC

import transcritor_core
from pydantic import JsonValue
from transcritor_core import ScoreDoc, run_stage
from transcritor_core.models import DocWarning, Location, WarningCode


class AddWarningStage:
    name = "dummy"
    version = "0.0.1"

    def run(self, doc: ScoreDoc, config: Mapping[str, JsonValue]) -> ScoreDoc:
        doc.warnings.append(
            DocWarning(
                code=WarningCode.LOW_CONFIDENCE_NOTE,
                severity="info",
                location=Location(),
                message="w",
            )
        )
        return doc


class MutatingStage:
    name = "mutator"
    version = "0.0.1"

    def run(self, doc: ScoreDoc, config: Mapping[str, JsonValue]) -> ScoreDoc:
        doc.parts.clear()
        doc.warnings.append(
            DocWarning(
                code=WarningCode.LOW_CONFIDENCE_NOTE,
                severity="info",
                location=Location(),
                message="x",
            )
        )
        return doc.model_copy(deep=True)


def test_provenance_appended_and_input_untouched(make_doc: Callable[[], ScoreDoc]) -> None:
    doc = make_doc()
    out = run_stage(AddWarningStage(), doc, {"k": 1}, adapter="stub")
    assert doc.provenance == [] and doc.warnings == []
    entry = out.provenance[-1]
    assert entry.stage == "dummy" and entry.params == {"k": 1}
    assert entry.module_version == "0.0.1" and entry.adapter == "stub"
    assert entry.duration_ms >= 0
    assert entry.started_at.tzinfo is not None
    assert entry.started_at.utcoffset() == UTC.utcoffset(None)
    assert len(out.warnings) == 1


def test_stage_mutating_input_does_not_leak(make_doc: Callable[[], ScoreDoc]) -> None:
    doc = make_doc()
    before = doc.model_copy(deep=True)
    run_stage(MutatingStage(), doc, {})
    assert doc == before


def test_provenance_accumulates(make_doc: Callable[[], ScoreDoc]) -> None:
    out = run_stage(AddWarningStage(), run_stage(AddWarningStage(), make_doc(), {}), {})
    assert len(out.provenance) == 2


def test_public_api_resolves() -> None:
    for name in transcritor_core.__all__:
        assert hasattr(transcritor_core, name), name
    assert transcritor_core.instruments.get("flute").name == "flute"
