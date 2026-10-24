"""Stage protocol: every pipeline module is a Stage run through ``run_stage``."""

import time
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Protocol

from pydantic import JsonValue, ValidationError

from transcritor_core.errors import StageOutputError
from transcritor_core.models import ProvenanceEntry, ScoreDoc


class Stage(Protocol):
    name: str
    version: str

    def run(self, doc: ScoreDoc, config: Mapping[str, JsonValue]) -> ScoreDoc: ...


def run_stage(
    stage: Stage,
    doc: ScoreDoc,
    config: Mapping[str, JsonValue],
    adapter: str | None = None,
) -> ScoreDoc:
    """Run ``stage`` on a deep copy of ``doc``, re-validate its output, append provenance.

    In-place mutations (e.g. appending to a list) bypass Pydantic validation, so the result
    is validated again; a contract violation raises ``StageOutputError``.
    """
    started_at = datetime.now(UTC)
    t0 = time.perf_counter()
    output = stage.run(doc.model_copy(deep=True), config)
    duration_ms = (time.perf_counter() - t0) * 1000.0
    try:
        result = ScoreDoc.model_validate(output.model_dump(mode="python"))
    except ValidationError as exc:
        raise StageOutputError(
            f"stage {stage.name!r} returned an invalid ScoreDoc: {exc}", stage=stage.name
        ) from exc
    result.provenance.append(
        ProvenanceEntry(
            stage=stage.name,
            module_version=stage.version,
            adapter=adapter,
            params=dict(config),
            started_at=started_at,
            duration_ms=duration_ms,
        )
    )
    return result
