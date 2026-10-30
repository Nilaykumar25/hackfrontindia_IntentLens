"""Apply schema.cypher to the configured Neo4j database.

All statements use IF NOT EXISTS so this script is fully idempotent —
safe to run on an already-populated database.

Usage:
    python -m scripts.apply_schema
"""
from __future__ import annotations

import os
import sys

SCHEMA = os.path.join("backend", "app", "graph", "schema.cypher")


def _statements() -> list[str]:
    with open(SCHEMA, encoding="utf-8") as f:
        raw = f.read()
    return [s.strip() for s in raw.split(";") if s.strip()]


def main() -> None:
    # ── connect ──────────────────────────────────────────────────────────────
    try:
        from backend.app.graph.db import get_db
        from neo4j.exceptions import AuthError, ServiceUnavailable
        db = get_db()
        ver = db.version()
        print(f"Connected to Neo4j {ver}")
    except AuthError as exc:
        print(f"\n[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)
    except ServiceUnavailable as exc:
        print(f"\n[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"\n[ERROR] Unexpected connection error: {exc}", file=sys.stderr)
        sys.exit(1)

    # ── apply statements ─────────────────────────────────────────────────────
    stmts = _statements()
    errors: list[tuple[str, Exception]] = []
    for stmt in stmts:
        label = stmt[:80].replace("\n", " ")
        try:
            db.run(stmt)
            print(f"  OK  {label}")
        except Exception as exc:
            print(f"  ERR {label}\n      → {exc}", file=sys.stderr)
            errors.append((stmt, exc))

    if errors:
        print(f"\n[FAIL] {len(errors)} statement(s) failed — see above.", file=sys.stderr)
        sys.exit(1)

    # ── verify: show final index state ────────────────────────────────────────
    print("\nIndex / constraint state after apply:")
    rows = db.run(
        "SHOW INDEXES YIELD name, type, state, labelsOrTypes, properties "
        "RETURN name, type, state, labelsOrTypes, properties "
        "ORDER BY type, name"
    )
    if not rows:
        print("  (no indexes found — unexpected)")
    for r in rows:
        status = "✓" if r["state"] == "ONLINE" else f"! {r['state']}"
        print(f"  [{status}] {r['type']:12s}  {r['name']}")

    pending = [r for r in rows if r["state"] != "ONLINE"]
    if pending:
        print(f"\n  {len(pending)} index(es) still populating — re-run `make schema` in a few seconds.")
    else:
        print(f"\n[PASS] All {len(rows)} indexes ONLINE.")


if __name__ == "__main__":
    main()
