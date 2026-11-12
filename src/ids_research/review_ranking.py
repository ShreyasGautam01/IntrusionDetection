"""Stable top-budget selection for reliability scores."""
from __future__ import annotations

from collections.abc import Iterable

import numpy as np


def stable_review_selections(
    scores: np.ndarray,
    budgets: Iterable[float] = (0.01, 0.05, 0.10),
) -> dict[float, dict[str, object]]:
    """Rank high scores first; exact ties retain their input row-offset order.

    Each budget selects exactly ``floor(budget * N)`` rows. The reported tie
    count is the number of rows in the full score vector equal to the cutoff.
    """
    values = np.asarray(scores)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("scores must be a non-empty one-dimensional array")
    if not np.issubdtype(values.dtype, np.number) or not np.isfinite(values).all():
        raise ValueError("scores must be numeric and finite")
    budget_values = tuple(float(b) for b in budgets)
    if any(not np.isfinite(b) or b < 0 or b > 1 for b in budget_values):
        raise ValueError("budgets must be finite fractions in [0, 1]")
    order = np.argsort(-values, kind="mergesort")
    result: dict[float, dict[str, object]] = {}
    for budget in budget_values:
        count = int(np.floor(budget * values.size))
        selected = order[:count]
        cutoff = None if count == 0 else float(values[selected[-1]])
        ties = 0 if cutoff is None else int(np.count_nonzero(values == cutoff))
        result[budget] = {
            "selected_row_offsets": selected,
            "selected_rows": count,
            "cutoff_score": cutoff,
            "cutoff_tie_count": ties,
            "tie_break": "stable ascending input row offset",
        }
    return result


def ranked_binary_event_metrics(
    scores: np.ndarray,
    generic_errors: np.ndarray,
    attack_misses: np.ndarray,
    budgets: Iterable[float] = (0.01, 0.05, 0.10),
) -> dict[str, object]:
    """Compute both event AUPRCs and exact stable floor-budget captures from one ranking."""
    values = np.asarray(scores)
    errors = np.asarray(generic_errors, dtype=np.uint8)
    misses = np.asarray(attack_misses, dtype=np.uint8)
    if (values.ndim != 1 or values.size == 0 or not np.isfinite(values).all()
            or errors.shape != values.shape or misses.shape != values.shape
            or np.any(errors > 1) or np.any(misses > 1)):
        raise ValueError("scores and binary event vectors must be finite, nonempty, and shape-matched")
    budget_values = tuple(float(b) for b in budgets)
    if any(not np.isfinite(b) or b < 0 or b > 1 for b in budget_values):
        raise ValueError("budgets must be finite fractions in [0, 1]")

    order = np.argsort(-values, kind="mergesort")
    sorted_scores = values[order]
    group_ends = np.flatnonzero(sorted_scores[1:] != sorted_scores[:-1]) + 1
    group_ends = np.append(group_ends, len(values))

    def average_precision(events: np.ndarray) -> float | None:
        positive_count = int(events.sum(dtype=np.int64))
        if positive_count == 0:
            return None
        cumulative = np.cumsum(events[order], dtype=np.int64)
        cumulative_at_group = cumulative[group_ends - 1]
        group_positive = np.diff(np.concatenate(([0], cumulative_at_group)))
        precision = cumulative_at_group / group_ends
        return float(np.sum((group_positive / positive_count) * precision))

    selections = {}
    positive_misses = int(misses.sum(dtype=np.int64))
    for budget in budget_values:
        count = int(np.floor(budget * len(values)))
        selected = order[:count]
        cutoff = None if count == 0 else float(values[selected[-1]])
        tie_count = 0 if cutoff is None else int(np.count_nonzero(values == cutoff))
        captured = int(misses[selected].sum(dtype=np.int64)) if count else 0
        selections[str(budget)] = {
            "selected_rows": count,
            "cutoff_score": cutoff,
            "cutoff_tie_count": tie_count,
            "attack_miss_capture": (captured / positive_misses if positive_misses else None),
            "attack_miss_rows_captured": captured,
            "tie_break": "stable ascending input row offset",
        }
    return {
        "generic_error_auprc": average_precision(errors),
        "attack_miss_auprc": average_precision(misses),
        "ranking_endpoints_defined": bool(errors.any() and misses.any()),
        "attack_miss_rows": positive_misses,
        "review_budgets": selections,
    }
