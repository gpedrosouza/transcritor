"""Eval dataset manifest: item descriptions, path resolution and reference note CSVs."""

import csv
from pathlib import Path
from typing import Literal, NamedTuple

from pydantic import BaseModel, ConfigDict, field_validator
from transcritor_core import KeyHint, instruments


class RefNote(NamedTuple):
    onset_s: float
    offset_s: float
    pitch_midi: int


class Item(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    instrument: str
    audio: str  # relative to the audio root
    audio_sha256: str | None = None
    reference_notes: str  # CSV, relative to the manifest
    reference_score: str  # MusicXML, relative to the manifest
    reference_downbeats: str  # downbeats file, relative to the manifest
    key: KeyHint | None = None
    license: str
    source: str
    subsets: list[Literal["ci", "full"]]

    @field_validator("instrument")
    @classmethod
    def _known_instrument(cls, value: str) -> str:
        try:
            instruments.get(value)
        except KeyError as exc:
            raise ValueError(str(exc.args[0])) from None
        return value


class Manifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    audio_root: Literal["manifest", "data"]
    items: list[Item]


def load_manifest(path: Path) -> Manifest:
    return Manifest.model_validate_json(path.read_text(encoding="utf-8"))


def resolve_audio(manifest_path: Path, manifest: Manifest, item: Item, data_root: Path) -> Path:
    """Locate the item's audio file (existence is not checked)."""
    root = manifest_path.parent if manifest.audio_root == "manifest" else data_root
    return root / item.audio


def read_reference_notes(path: Path) -> list[RefNote]:
    with path.open(newline="", encoding="utf-8") as fh:
        return [
            RefNote(float(row["onset_s"]), float(row["offset_s"]), int(row["pitch_midi"]))
            for row in csv.DictReader(fh)
        ]
