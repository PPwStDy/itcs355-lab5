"""Shared contracts used by local and managed training steps."""

from __future__ import annotations

import pandas as pd
from src import data


def validate(frame: pd.DataFrame) -> None:
    missing, extra = set(data.SCHEMA) - set(frame), set(frame) - set(data.SCHEMA)
    if missing or extra:
        raise ValueError(f"Schema mismatch: missing={sorted(missing)}, unexpected={sorted(extra)}")
    for col, dtype in data.SCHEMA.items():
        if str(frame[col].dtype) != dtype:
            raise ValueError(f"{col}: expected {dtype}, got {frame[col].dtype}")
        if frame[col].isna().any():
            raise ValueError(f"{col}: null rate must be zero")
    for col, (lo, hi) in data.PLAUSIBLE_RANGES.items():
        if not frame[col].between(lo, hi).all():
            raise ValueError(f"{col}: outside [{lo}, {hi}]")
    if not frame[data.ID].is_unique:
        raise ValueError("Duplicate reading_id")
    if (
        not set(frame[data.TARGET].unique()) <= {0, 1}
        or not 0.01 < frame[data.TARGET].mean() < 0.99
    ):
        raise ValueError("Labels must be binary and nondegenerate")
