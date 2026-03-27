"""Dimension-based assessment scoring (ADR-150).

Pure Python — no Django, no DB. Fully unit-testable.
Reusable across coach-hub, risk-hub, and any future consumer.
"""

from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreResult:
    """Result for a single dimension."""

    dimension: str
    raw_score: float
    risk_level: str
    label: str


def _risk_level(score: float) -> str:
    """Map normalised score (0-1) to risk level."""
    if score >= 0.75:
        return "low"
    if score >= 0.5:
        return "medium"
    if score >= 0.25:
        return "high"
    return "critical"


def calculate_dimension_score(
    responses: list[dict],
) -> list[ScoreResult]:
    """Calculate weighted dimension scores from responses.

    Args:
        responses: list of dicts with keys:
            - dimension (str)
            - value (str|int|float, Likert 1-5)
            - weight (float, default 1.0)

    Returns:
        list of ScoreResult per dimension,
        sorted by raw_score ascending.
    """
    buckets: dict[str, list[tuple[float, float]]] = (
        defaultdict(list)
    )
    for r in responses:
        try:
            value = float(r["value"]) / 5.0
            weight = float(r.get("weight", 1.0))
            buckets[r["dimension"]].append((value, weight))
        except (KeyError, ValueError):
            continue

    results = []
    for dimension, items in buckets.items():
        total_weight = sum(w for _, w in items)
        if total_weight == 0:
            continue
        raw = sum(v * w for v, w in items) / total_weight
        pct = round(raw * 100, 1)
        results.append(
            ScoreResult(
                dimension=dimension,
                raw_score=pct,
                risk_level=_risk_level(raw),
                label=f"{dimension.title()}: {round(pct)}%",
            )
        )
    return sorted(results, key=lambda r: r.raw_score)
