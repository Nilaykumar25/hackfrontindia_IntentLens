"""Print graph statistics and run sanity checks.

Usage: python -m scripts.graph_stats

Prints:
  - Node counts by label
  - Relationship counts by type
  - Sanity checks: orphan commits, entities with no commits, duplicate persons
"""
from __future__ import annotations

import sys


def _fmt(n: int) -> str:
    return f"{n:>8,}"


def node_counts(db) -> dict[str, int]:
    rows = db.run(
        "CALL db.labels() YIELD label "
        "CALL { WITH label MATCH (n) WHERE label IN labels(n) RETURN count(n) AS cnt } "
        "RETURN label, cnt ORDER BY label"
    )
    return {r["label"]: r["cnt"] for r in rows}


def rel_counts(db) -> dict[str, int]:
    rows = db.run(
        "CALL db.relationshipTypes() YIELD relationshipType "
        "CALL { WITH relationshipType MATCH ()-[r]->() WHERE type(r) = relationshipType "
        "       RETURN count(r) AS cnt } "
        "RETURN relationshipType, cnt ORDER BY relationshipType"
    )
    return {r["relationshipType"]: r["cnt"] for r in rows}


def sanity_checks(db) -> list[dict]:
    checks = []

    # 1. Orphan commits: commits with no MODIFIES edges (no entities linked)
    r = db.run("MATCH (c:Commit) WHERE NOT (c)-[:MODIFIES]->() RETURN count(c) AS n")
    checks.append({"check": "Orphan commits (no MODIFIES)", "count": r[0]["n"]})

    # 2. Entities with no commits
    r = db.run("MATCH (e:Entity) WHERE NOT (e)<-[:MODIFIES]-(:Commit) RETURN count(e) AS n")
    checks.append({"check": "Entities with no commits", "count": r[0]["n"]})

    # 3. Duplicate persons (same name, different id)
    r = db.run(
        "MATCH (p:Person) WITH p.name AS name, count(*) AS cnt, collect(p.id) AS ids "
        "WHERE cnt > 1 RETURN count(*) AS n, collect(ids) AS dup_ids LIMIT 5"
    )
    checks.append({"check": "Duplicate person names", "count": r[0]["n"] if r else 0,
                   "detail": r[0]["dup_ids"][:3] if r else []})

    # 4. Documents with empty text
    r = db.run("MATCH (d:Document) WHERE d.text = '' OR d.text IS NULL RETURN count(d) AS n")
    checks.append({"check": "Documents with empty text", "count": r[0]["n"]})

    # 5. Self-referencing edges (should be 0)
    r = db.run("MATCH (n)-[r]->(n) RETURN count(r) AS n")
    checks.append({"check": "Self-referencing edges", "count": r[0]["n"]})

    # 6. Total node count
    r = db.run("MATCH (n) RETURN count(n) AS n")
    checks.append({"check": "Total nodes", "count": r[0]["n"]})

    # 7. Total relationship count
    r = db.run("MATCH ()-[r]->() RETURN count(r) AS n")
    checks.append({"check": "Total relationships", "count": r[0]["n"]})

    return checks


def main() -> None:
    from backend.app.graph.db import get_db

    print("=" * 60)
    print("  IntentLens — Graph Statistics")
    print("=" * 60)

    try:
        db = get_db()
        ver = db.version()
        print(f"  Neo4j {ver}\n")
    except Exception as exc:
        print(f"  [ERROR] {exc}", file=sys.stderr)
        sys.exit(1)

    # ── Node counts ────────────────────────────────────────────────────────
    print("── Node counts by label ──")
    nc = node_counts(db)
    total_nodes = 0
    for label, count in nc.items():
        print(f"  {_fmt(count)}  {label}")
        total_nodes += count
    print(f"  {'─' * 30}")
    print(f"  {_fmt(total_nodes)}  TOTAL")

    # ── Relationship counts ──────────────────────────────────────────────────
    print("\n── Relationship counts by type ──")
    rc = rel_counts(db)
    total_rels = 0
    for rtype, count in rc.items():
        print(f"  {_fmt(count)}  {rtype}")
        total_rels += count
    print(f"  {'─' * 30}")
    print(f"  {_fmt(total_rels)}  TOTAL")

    # ── Sanity checks ───────────────────────────────────────────────────────
    print("\n── Sanity checks ──")
    checks = sanity_checks(db)
    for c in checks:
        flag = "  " if c["count"] == 0 or c["check"].startswith("Total") else "⚠ "
        print(f"  {flag}{c['check']:40s}  {_fmt(c['count'])}")
        if c.get("detail"):
            print(f"       examples: {c['detail']}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
