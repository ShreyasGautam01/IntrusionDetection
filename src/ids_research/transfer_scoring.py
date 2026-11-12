"""Frozen binary reliability-signal calculations for target transfer batches."""
from __future__ import annotations

import numpy as np
from threadpoolctl import threadpool_limits


def reliability_score_batch(
    model,
    calibrator,
    isolation_forest,
    features: np.ndarray,
    *,
    conformal_quantile: float,
    thread_limit: int = 1,
) -> dict[str, np.ndarray]:
    """Score one feature-only batch using the five frozen E1 signal definitions."""
    x = np.asarray(features)
    if x.ndim != 2 or x.shape[0] < 1 or x.dtype != np.float32:
        raise ValueError("Target scoring requires a nonempty float32 feature matrix")
    if not np.isfinite(x).all():
        raise ValueError("Target feature batch contains a non-finite value")
    if not np.isfinite(conformal_quantile) or not 0 <= conformal_quantile <= 1:
        raise ValueError("Source-fitted conformal quantile is invalid")
    if not isinstance(thread_limit, int) or isinstance(thread_limit, bool) or thread_limit < 1:
        raise ValueError("thread_limit must be a positive integer")
    if not getattr(model, "estimators_", None):
        raise ValueError("Random forest has no fitted trees")

    with threadpool_limits(limits=thread_limit):
        raw_probability = np.clip(model.predict_proba(x)[:, 1], 1e-7, 1 - 1e-7)
        logits = np.log(raw_probability / (1 - raw_probability)).reshape(-1, 1)
        probability = calibrator.predict_proba(logits)[:, 1].astype(np.float32)
        confidence = (1 - np.maximum(probability, 1 - probability)).astype(np.float32)

        votes = np.zeros((len(x), 2), dtype=np.uint8)
        rows = np.arange(len(x))
        for tree in model.estimators_:
            prediction = tree.predict(x).astype(np.uint8, copy=False)
            if prediction.shape != (len(x),) or np.any(prediction > 1):
                raise ValueError("Random forest tree emitted a malformed binary prediction batch")
            votes[rows, prediction] += 1
        disagreement = (1 - votes.max(axis=1).astype(np.float32)
                        / len(model.estimators_)).astype(np.float32)

        class_probability = np.column_stack((probability, 1 - probability))
        prediction_set = (1 - class_probability) <= conformal_quantile
        conformal = (prediction_set.sum(axis=1).astype(np.float32) - 1).astype(np.float32)
        isolation = (-isolation_forest.score_samples(x)).astype(np.float32)

    result = {
        "calibrated_probability": probability,
        "confidence": confidence,
        "random_forest_disagreement": disagreement,
        "split_conformal": conformal,
        "isolation_forest": isolation,
    }
    if any(value.shape != (len(x),) or not np.isfinite(value).all()
           for value in result.values()):
        raise ValueError("Target reliability output is malformed or non-finite")
    return result
