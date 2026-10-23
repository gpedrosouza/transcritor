"""Note-level and downbeat metrics (mir_eval) comparing a ScoreDoc to a reference."""

import warnings

import mir_eval
import numpy as np
from pydantic import BaseModel, ConfigDict
from transcritor_core import ScoreDoc, midi_to_hz

from transcritor_eval.dataset import RefNote

ONSET_TOLERANCE_S = 0.05
PITCH_TOLERANCE_CENTS = 50.0
OFFSET_RATIO = 0.2


class NoteMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    onset_precision: float
    onset_recall: float
    onset_f1: float
    offset_f1: float
    downbeat_f1: float


def downbeat_f1(reference_s: list[float], estimate_s: list[float]) -> float:
    """F-measure (70 ms window); the last reference time is the end instant, not a downbeat."""
    ref = np.asarray(reference_s[:-1], dtype=float)
    est = np.asarray(estimate_s, dtype=float)
    if ref.size == 0 or est.size == 0:
        return 0.0
    return float(mir_eval.beat.f_measure(ref, est))


def note_metrics(
    reference: list[RefNote], reference_downbeats_s: list[float], doc: ScoreDoc
) -> NoteMetrics:
    downbeats = downbeat_f1(reference_downbeats_s, doc.timeline.downbeats_s)
    est_notes = [n for part in doc.parts for n in part.notes]
    if not reference or not est_notes:
        return NoteMetrics(
            onset_precision=0.0,
            onset_recall=0.0,
            onset_f1=0.0,
            offset_f1=0.0,
            downbeat_f1=downbeats,
        )
    ref_iv = np.array([[n.onset_s, n.offset_s] for n in reference], dtype=float)
    ref_hz = np.array([midi_to_hz(n.pitch_midi) for n in reference], dtype=float)
    est_iv = np.array([[n.onset_s, n.offset_s] for n in est_notes], dtype=float)
    est_hz = np.array([midi_to_hz(n.pitch_midi) for n in est_notes], dtype=float)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        precision, recall, onset_f1, _ = mir_eval.transcription.precision_recall_f1_overlap(
            ref_iv,
            ref_hz,
            est_iv,
            est_hz,
            onset_tolerance=ONSET_TOLERANCE_S,
            pitch_tolerance=PITCH_TOLERANCE_CENTS,
            offset_ratio=None,
        )
        _, _, offset_f1, _ = mir_eval.transcription.precision_recall_f1_overlap(
            ref_iv,
            ref_hz,
            est_iv,
            est_hz,
            onset_tolerance=ONSET_TOLERANCE_S,
            pitch_tolerance=PITCH_TOLERANCE_CENTS,
            offset_ratio=OFFSET_RATIO,
        )
    return NoteMetrics(
        onset_precision=float(precision),
        onset_recall=float(recall),
        onset_f1=float(onset_f1),
        offset_f1=float(offset_f1),
        downbeat_f1=downbeats,
    )
