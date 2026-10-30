"""Print every SUPERSEDES / REFINES / REVERTS edge with full context.

Usage: python -m scripts.show_supersession
"""
from __future__ import annotations
from backend.app.graph.db import get_db

QUERY = """
MATCH (newer:Decision)-[r:SUPERSEDES|REFINES|REVERTS]->(older:Decision)
RETURN
  type(r) AS edge_type,
  r.confidence AS confidence,
  r.reason AS reason,
  newer.id AS newer_id, newer.title AS newer_title, newer.decided_on AS newer_date, newer.status AS newer_status,
  older.id AS older_id, older.title AS older_title, older.decided_on AS older_date, older.status AS older_status
ORDER BY edge_type, r.confidence DESC
"""


def main() -> None:
    db = get_db()
    rows = db.run(QUERY)

    if not rows:
        print("No supersession edges in the graph yet.")
        return

    print(f"{'=' * 80}")
    print(f"  Supersession edges ({len(rows)} total)")
    print(f"{'=' * 80}\n")

    for i, r in enumerate(rows, 1):
        edge = r["edge_type"]
        conf = r["confidence"]
        reason = r["reason"] or "(no reason stored)"
        n_date = (r["newer_date"] or "?")[:10]
        o_date = (r["older_date"] or "?")[:10]

        marker = {"SUPERSEDES": "▶ SUPERSEDES", "REVERTS": "↩ REVERTS", "REFINES": "⊂ REFINES"}.get(edge, edge)
        print(f"[{i}] {marker}  confidence={conf:.3f}")
        print(f"  NEWER  {n_date}  [{r['newer_status']:10}]  {r['newer_id'][:8]}  {r['newer_title']}")
        print(f"    {marker.center(12)} →")
        print(f"  OLDER  {o_date}  [{r['older_status']:10}]  {r['older_id'][:8]}  {r['older_title']}")
        print(f"  Reason: {reason}")
        print()

    # Summary
    by_type: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for r in rows:
        by_type[r["edge_type"]] = by_type.get(r["edge_type"], 0) + 1
        by_status[r["older_status"]] = by_status.get(r["older_status"], 0) + 1

    print(f"{'─' * 60}")
    print("Edge type counts:")
    for t, n in sorted(by_type.items()):
        print(f"  {t:12s}  {n}")
    print("\nOlder-decision statuses:")
    for s, n in sorted(by_status.items()):
        print(f"  {s:12s}  {n}")


if __name__ == "__main__":
    main()
