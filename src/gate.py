"""Fail closed unless a candidate clears an absolute floor and an explicit incumbent."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Decision:
    passed: bool
    reason: str
    candidate: float
    incumbent: float | None
    floor: float
    margin: float

    def as_dict(self):
        return asdict(self)


def evaluate(
    candidate: float, incumbent: float | None, *, bootstrap=False, floor=0.75, margin=0.01
) -> Decision:
    values = [candidate, floor, margin] + ([] if incumbent is None else [incumbent])
    if not all(math.isfinite(v) for v in values):
        raise ValueError("Gate values must be finite")
    if not 0 <= candidate <= 1 or not 0 <= floor <= 1 or not 0 < margin <= 1:
        raise ValueError("Invalid probability floor, score or promotion margin")
    if incumbent is not None and not 0 <= incumbent <= 1:
        raise ValueError("Invalid incumbent score")
    if candidate < floor:
        reason = "candidate below absolute floor"
    elif incumbent is None and not bootstrap:
        reason = "incumbent unavailable; explicit first-registration approval required"
    elif incumbent is not None and candidate - incumbent < margin:
        reason = "improvement smaller than promotion margin"
    else:
        return Decision(
            True,
            "explicit bootstrap" if incumbent is None else "floor and margin passed",
            candidate,
            incumbent,
            floor,
            margin,
        )
    return Decision(False, reason, candidate, incumbent, floor, margin)
