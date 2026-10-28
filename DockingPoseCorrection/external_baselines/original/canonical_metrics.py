"""Verbatim scientific primitives from ``docking_correction.metrics``.

This minimal copy keeps the external-baseline bundle self-contained while
preserving the project's frozen Equation 4 definition.  It deliberately does
not perform rigid-body alignment or any tool-specific coordinate adjustment.
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np


METRIC_VERSION = "metrics-v1"


class MetricsError(ValueError):
    """A metric input violates its scientific contract."""


def _paired_coordinates(
    pred: Sequence[Sequence[float]] | np.ndarray,
    target: Sequence[Sequence[float]] | np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    predicted = np.asarray(pred, dtype=np.float64)
    expected = np.asarray(target, dtype=np.float64)
    if predicted.ndim != 2 or predicted.shape[1] != 3 or predicted.shape[0] == 0:
        raise MetricsError("pred must have shape (N, 3) with N > 0")
    if expected.shape != predicted.shape:
        raise MetricsError("target must have the same (N, 3) shape as pred")
    if not np.isfinite(predicted).all() or not np.isfinite(expected).all():
        raise MetricsError("coordinate arrays contain non-finite values")
    return predicted, expected


def mean_squared_displacement(
    pred: Sequence[Sequence[float]] | np.ndarray,
    target: Sequence[Sequence[float]] | np.ndarray,
) -> float:
    """Return ``mean_i ||pred_i - target_i||^2`` (frozen Equation 4)."""

    predicted, expected = _paired_coordinates(pred, target)
    return float(np.mean(np.sum(np.square(predicted - expected), axis=1)))


def pose_rmsd(
    pred: Sequence[Sequence[float]] | np.ndarray,
    target: Sequence[Sequence[float]] | np.ndarray,
) -> float:
    """Return the sole RMSD definition authorized for success thresholds."""

    return math.sqrt(mean_squared_displacement(pred, target))
