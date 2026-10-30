"""Confidence from graph facts. Pure functions so they are unit-testable without Neo4j or an LLM."""
from __future__ import annotations
from ..config import settings
from ..models import Confidence, Factors

WEIGHTS = {"directness": 0.30, "corroboration": 0.25, "agreement": 0.20, "currency": 0.15, "distance": 0.10}
HIGH, MEDIUM = 0.75, 0.55


def corroboration_score(n_sources: int) -> float:
    return {0: 0.0, 1: 0.4, 2: 0.7}.get(n_sources, 1.0)


def distance_score(hops: int, max_hops: int | None = None) -> float:
    max_hops = max_hops or settings.max_graph_hops
    return max(0.0, min(1.0, 1 - (hops - 1) / max_hops))


def currency_score(drift_commits: int) -> float:
    return 1 - min(1.0, drift_commits / 5)


def score(f: Factors) -> float:
    return round(sum(WEIGHTS[k] * getattr(f, k) for k in WEIGHTS), 3)


def label_for(s: float, has_decision: bool = True, threshold: float | None = None) -> str:
    threshold = settings.refusal_threshold if threshold is None else threshold
    if not has_decision or s < threshold:
        return "No answer"
    if s >= HIGH:
        return "High"
    if s >= MEDIUM:
        return "Medium"
    return "Low"


def reasons(f: Factors, drift: int, n_sources: int, currency_unknown: bool = False) -> list[str]:
    r = []
    r.append("Rationale is stated explicitly in the source." if f.directness >= 1 else "Rationale is inferred, not stated outright.")
    r.append(f"{n_sources} independent source type(s) support this decision.")
    r.append("Two extraction passes agree." if f.agreement >= 0.8 else "Extraction passes only partly agree.")
    if currency_unknown:
        r.append("Could not measure code drift: the decision has no linked code entities.")
    elif drift == 0:
        r.append("Code still matches the decision.")
    else:
        r.append(f"{drift} later change(s) touched this entity without a recorded decision (possible drift).")
    r.append("Directly linked to the entity." if f.distance >= 0.99 else "Linked to the entity through a looser semantic match.")
    return r


def build(f: Factors, drift: int, n_sources: int, has_decision: bool = True, currency_unknown: bool = False) -> Confidence:
    s = score(f)
    return Confidence(score=s, label=label_for(s, has_decision), factors=f, reasons=reasons(f, drift, n_sources, currency_unknown))
