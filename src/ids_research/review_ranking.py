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
