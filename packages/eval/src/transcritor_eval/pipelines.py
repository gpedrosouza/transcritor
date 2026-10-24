"""Pipelines under evaluation: callables turning an audio file plus hints into a ScoreDoc."""

import hashlib
from collections.abc import Callable, Mapping
from pathlib import Path

import soundfile
from pydantic import JsonValue
from transcritor_core import AudioInfo, Hints, Part, ScoreDoc, Source, run_stage

import transcritor_eval

Pipeline = Callable[[Path, Hints], ScoreDoc]


class _NullStage:
    name = "null"
    version = transcritor_eval.__version__

    def __init__(self, hints: Hints) -> None:
        self._hints = hints

    def run(self, doc: ScoreDoc, config: Mapping[str, JsonValue]) -> ScoreDoc:
        doc.parts = [
            Part.from_instrument(f"p{i}", entry.instrument)
            for i, entry in enumerate(self._hints.instruments, start=1)
        ]
        return doc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def null_pipeline(audio_path: Path, hints: Hints) -> ScoreDoc:
    """Baseline that transcribes nothing: an empty document with one part per hinted instrument.

    The ``count`` of each ``InstrumentCount`` is ignored for now: one part per entry.
    """
    info = soundfile.info(str(audio_path))
    audio = AudioInfo(
        sha256=_sha256(audio_path),
        duration_s=info.frames / info.samplerate,
        sample_rate=info.samplerate,
        channels=info.channels,
        original_name=audio_path.name,
    )
    doc = ScoreDoc.new(source=Source(audio=audio, hints=hints))
    return run_stage(_NullStage(hints), doc, {})


PIPELINES: dict[str, Pipeline] = {"null": null_pipeline}
