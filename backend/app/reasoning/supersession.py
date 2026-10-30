"""Supersession engine: structural (reverts), semantic (LLM pair classification), temporal (status resolution).

Pair selection strategy (Task 16):
  1. Per-entity consecutive pairs (existing): for any entity with ≥2 governing decisions,
     classify each consecutive (older, newer) pair in date order.
  2. Cross-entity high-similarity pairs (new): any two decisions whose embeddings have
     cosine similarity ≥ EMBED_SIM_THRESHOLD are also candidates, regardless of shared
     entity, as long as they haven't been classified already. This catches supersessions
     between decisions that govern different (or no) entities.
  LLM call cap: capped at MAX_LLM_CALLS total to control token spend.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from ..extraction.entities import find_reverted_sha
from ..graph.db import Neo4jDB
from ..llm.provider import LLM, cosine

log = logging.getLogger(__name__)

MIN_CONF = 0.6
EMBED_SIM_THRESHOLD = 0.50   # cosine similarity threshold for cross-entity candidate pairs
MAX_LLM_CALLS = 200           # hard cap on classify_pair calls per run_supersession call


CLASSIFY_SYSTEM = """You compare two engineering decisions from the Redis project.
OLDER was made first, NEWER was made later. Classify how NEWER relates to OLDER:

- "reinforces": NEWER confirms or repeats the same choice without changing it
- "refines":    NEWER narrows, extends, or adjusts OLDER without discarding it
- "contradicts": NEWER replaces or overrides OLDER so OLDER no longer holds
- "unrelated":  NEWER is about a completely different concern

Rules:
- Base your classification only on the text provided.
- "contradicts" requires that NEWER explicitly reverses a specific choice in OLDER.
- If you are unsure, choose "unrelated" with low confidence rather than guess.
- Return ONLY valid JSON with no extra text.

Return JSON: {"relation": "reinforces"|"refines"|"contradicts"|"unrelated", "confidence": 0.0-1.0, "reason": "one sentence max 200 chars"}"""


@dataclass
class Link:
    newer: str
    older: str
    kind: str          # SUPERSEDES | REFINES | REVERTS
    confidence: float
    reason: str = ""


def compute_statuses(
    decision_ids: list[str],
    links: list[Link],
    min_conf: float = MIN_CONF,
) -> dict[str, str]:
    """Pure status resolution. Precedence: SUPERSEDED/REVERSED > UNCERTAIN > ACTIVE."""
    status = {d: "ACTIVE" for d in decision_ids}
    for lnk in links:
        if lnk.older not in status or lnk.kind == "REFINES":
            continue
        strong = lnk.confidence >= min_conf
        if lnk.kind == "REVERTS" and strong:
            status[lnk.older] = "REVERSED"
        elif lnk.kind == "SUPERSEDES" and strong and status[lnk.older] != "REVERSED":
            status[lnk.older] = "SUPERSEDED"
        elif status[lnk.older] == "ACTIVE":
            status[lnk.older] = "UNCERTAIN"
    return status


def find_reverts(commits: list[dict]) -> list[tuple[str, str]]:
    """Return [(reverting_sha, reverted_sha_prefix)] from commit messages."""
    out = []
    for c in commits:
        sha = find_reverted_sha(c.get("message", ""))
        if sha:
            out.append((c["sha"], sha))
    return out


def classify_pair(llm: LLM, older: dict, newer: dict) -> Link | None:
    """Ask the LLM to classify the relationship between two decisions.

    Returns a Link or None (if LLM fails or returns unrelated/reinforces).
    Only SUPERSEDES (contradicts) and REFINES are materialised as edges.
    """
    user = (
        f"OLDER decision ({(older.get('decided_on') or '?')[:10]}):\n"
        f"Title: {older['title']}\n"
        f"Summary: {older['summary']}\n"
        f"Rationale: {older.get('rationale') or ''}\n\n"
        f"NEWER decision ({(newer.get('decided_on') or '?')[:10]}):\n"
        f"Title: {newer['title']}\n"
        f"Summary: {newer['summary']}\n"
        f"Rationale: {newer.get('rationale') or ''}"
    )
    try:
        r = llm.complete_json(CLASSIFY_SYSTEM, user, 600)
    except Exception as exc:
        log.warning("classify_pair LLM error: %s", exc)
        return None

    rel = r.get("relation", "")
    try:
        conf = float(r.get("confidence", 0))
    except (TypeError, ValueError):
        conf = 0.0

    kind = {"contradicts": "SUPERSEDES", "refines": "REFINES"}.get(rel)
    if not kind:
        return None
    return Link(newer["id"], older["id"], kind, conf, r.get("reason", "")[:200])


# ── Cypher templates for persisting edges ─────────────────────────────────────

EDGE = {
    "SUPERSEDES": (
        "MATCH (n:Decision {id:$n}),(o:Decision {id:$o}) "
        "MERGE (n)-[r:SUPERSEDES]->(o) "
        "SET r.reason=$reason, r.confidence=$conf"
    ),
    "REFINES": (
        "MATCH (n:Decision {id:$n}),(o:Decision {id:$o}) "
        "MERGE (n)-[r:REFINES]->(o) "
        "SET r.reason=$reason, r.confidence=$conf"
    ),
    "REVERTS": (
        "MATCH (n:Decision {id:$n}),(o:Decision {id:$o}) "
        "MERGE (n)-[r:REVERTS]->(o) "
        "SET r.reason=$reason, r.confidence=$conf"
    ),
}


# ── Main entry point ──────────────────────────────────────────────────────────

def run_supersession(db: Neo4jDB, llm: LLM) -> dict:
    """Run all three supersession signals and persist edges + statuses.

    Returns a summary dict with counts.
    """
    ids = [r["id"] for r in db.run("MATCH (d:Decision) RETURN d.id AS id")]
    links: list[Link] = []
    llm_calls = 0

    # ── 1) Structural: commit reverts ──────────────────────────────────────────
    revert_commits = db.run(
        "MATCH (c:Commit) WHERE c.message CONTAINS 'This reverts commit' "
        "RETURN c.id AS sha, c.message AS message"
    )
    n_revert_commits = len(revert_commits)
    for rev_sha, target in find_reverts(revert_commits):
        # Find decisions evidenced by the reverting commit
        newer_decisions = db.run(
            "MATCH (d:Decision) WHERE "
            "  EXISTS { MATCH (d)-[:EVIDENCED_BY]->(c:Commit {id:$sha}) } OR "
            "  EXISTS { MATCH (c:Commit {id:$sha})-[:PART_OF]->(t)<-[:EVIDENCED_BY]-(d) } "
            "RETURN d.id AS id, d.decided_on AS date",
            sha=rev_sha,
        )
        # Find decisions evidenced by the reverted commit (sha prefix match)
        older_decisions = db.run(
            "MATCH (d:Decision)-[:EVIDENCED_BY]->(c:Commit) WHERE c.id STARTS WITH $p "
            "RETURN d.id AS id "
            "UNION "
            "MATCH (c:Commit)-[:PART_OF]->(t)<-[:EVIDENCED_BY]-(d:Decision) WHERE c.id STARTS WITH $p "
            "RETURN d.id AS id",
            p=target,
        )
        for n in newer_decisions:
            for o in older_decisions:
                if n["id"] != o["id"]:
                    reason = f"Commit {rev_sha[:8]} reverts {target[:8]}"
                    links.append(Link(n["id"], o["id"], "REVERTS", 0.95, reason))

    log.info("Structural: %d revert commits → %d REVERTS links", n_revert_commits, len(links))

    # ── 2a) Semantic: per-entity consecutive pairs ─────────────────────────────
    done: set[tuple[str, str]] = set()
    per_entity_pairs = 0

    groups = db.run(
        "MATCH (d:Decision)-[:GOVERNS]->(e:Entity) "
        "WITH e, collect(DISTINCT d) AS ds "
        "WHERE size(ds) >= 2 "
        "RETURN e.id AS entity, "
        "  [x IN ds | x{.id,.title,.summary,.rationale,.decided_on,.embedding}] AS decisions"
    )
    for g in groups:
        ds = sorted(g["decisions"], key=lambda x: x.get("decided_on") or "")
        for older, newer in zip(ds, ds[1:]):
            key = (older["id"], newer["id"])
            if key in done or llm_calls >= MAX_LLM_CALLS:
                continue
            done.add(key)
            lnk = classify_pair(llm, older, newer)
            llm_calls += 1
            per_entity_pairs += 1
            if lnk:
                links.append(lnk)

    # ── 2b) Semantic: cross-entity high-similarity pairs ──────────────────────
    # Fetch all decisions with embeddings
    all_decisions = db.run(
        "MATCH (d:Decision) WHERE d.embedding IS NOT NULL "
        "RETURN d.id AS id, d.title AS title, d.summary AS summary, "
        "       d.rationale AS rationale, d.decided_on AS decided_on, "
        "       d.embedding AS embedding"
    )

    high_sim_pairs = 0
    if len(all_decisions) >= 2:
        # Compare every pair, keep those with cosine > threshold
        for i, da in enumerate(all_decisions):
            for j, db_ in enumerate(all_decisions):
                if i >= j:
                    continue
                if llm_calls >= MAX_LLM_CALLS:
                    break
                if not da.get("embedding") or not db_.get("embedding"):
                    continue
                sim = cosine(da["embedding"], db_["embedding"])
                if sim < EMBED_SIM_THRESHOLD:
                    continue
                # Sort by date: older first
                da_date = da.get("decided_on") or ""
                db_date = db_.get("decided_on") or ""
                older_d, newer_d = (da, db_) if da_date <= db_date else (db_, da)
                key = (older_d["id"], newer_d["id"])
                if key in done:
                    continue
                done.add(key)
                lnk = classify_pair(llm, older_d, newer_d)
                llm_calls += 1
                high_sim_pairs += 1
                if lnk:
                    links.append(lnk)

    log.info(
        "Semantic: %d per-entity pairs + %d high-similarity pairs = %d LLM calls → %d edges",
        per_entity_pairs, high_sim_pairs, llm_calls, len(links) - n_revert_commits,
    )

    # ── 3) Temporal: status resolution + persist ──────────────────────────────
    for lnk in links:
        db.run(EDGE[lnk.kind], n=lnk.newer, o=lnk.older, reason=lnk.reason, conf=lnk.confidence)

    statuses = compute_statuses(ids, links)
    db.run(
        "UNWIND $rows AS r MATCH (d:Decision {id:r.id}) SET d.status=r.status",
        rows=[{"id": k, "status": v} for k, v in statuses.items()],
    )

    non_active = sum(1 for s in statuses.values() if s != "ACTIVE")
    log.info("Status resolution: %d total, %d non-active", len(ids), non_active)

    return {
        "decisions": len(ids),
        "revert_commits_checked": n_revert_commits,
        "links": len(links),
        "llm_calls": llm_calls,
        "non_active": non_active,
    }
