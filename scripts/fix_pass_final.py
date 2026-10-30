"""Fix remaining items: doc tagging, refusal entity, demoQuestions update."""
import sys
sys.path.insert(0, '.')
import httpx
from backend.app.graph.db import get_db

BASE = "http://127.0.0.1:8000"
db   = get_db()

def ask(q):
    r = httpx.post(f"{BASE}/ask", json={"question": q}, timeout=90)
    return r.json()

# ─────────────────────────────────────────────────────────────────────────────
# Fix Item 6: tag 'other' documents properly
# The earlier run returned (none) — the SET worked but the MATCH clause
# may have been filtering differently. Force it via two passes.
# ─────────────────────────────────────────────────────────────────────────────
print("=== Item 6: Force-tag legacy documents as 'other' ===")

# Tag documents that have no source_kind (null) or empty string
n1 = db.run("""
MATCH (d:Document)
WHERE d.source_kind IS NULL
SET d.source_kind = 'other'
RETURN count(d) AS n
""")[0]["n"]
print(f"  Tagged null source_kind: {n1}")

n2 = db.run("""
MATCH (d:Document)
WHERE d.source_kind = ''
SET d.source_kind = 'other'
RETURN count(d) AS n
""")[0]["n"]
print(f"  Tagged empty source_kind: {n2}")

dist = db.run("""
MATCH (d:Document)
RETURN d.source_kind AS sk, count(d) AS n
ORDER BY n DESC
""")
print("  Distribution:")
for r in dist:
    print(f"    {r['sk']:<35} {r['n']}")

# ─────────────────────────────────────────────────────────────────────────────
# Item 4: Find refusal entity — try functions that are LESS likely to
# be hit by entity linking (not in a PR title or commit subject).
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== Item 4: Find reliable refusal entity ===")

# Try functions that have no Decision and return refused
candidates = db.run("""
MATCH (e:Function)<-[:MODIFIES]-(c:Commit)
WHERE NOT EXISTS { MATCH (d:Decision)-[:GOVERNS]->(e) }
WITH e, count(c) AS n
WHERE n >= 3
RETURN e.id AS id, e.name AS name, e.path AS path, n
ORDER BY n DESC
LIMIT 20
""")
print(f"Candidates: {len(candidates)}")

# Test each until we find one that returns status=refused
best_refused = None
for r in candidates:
    fn = r["name"]
    q  = f"What design decision explains why {fn} uses its current implementation strategy?"
    b  = ask(q)
    if b["status"] == "refused":
        best_refused = (fn, r["path"], r["n"], q, b)
        print(f"  ✓ REFUSED: {fn!r} ({r['n']} commits)")
        print(f"    question: {q!r}")
        changers = [(x.get('author',''), x.get('date','')[:10]) for x in b.get('related',[])[:3]]
        print(f"    last_changers: {changers}")
        break
    else:
        print(f"  ✗ not refused ({b['status']}): {fn!r}")

if not best_refused:
    # Fall back: use a ConfigKey with no decision
    ck_cands = db.run("""
    MATCH (e:ConfigKey)<-[:MODIFIES]-(c:Commit)
    WHERE NOT EXISTS { MATCH (d:Decision)-[:GOVERNS]->(e) }
    WITH e, count(c) AS n WHERE n >= 3
    RETURN e.id AS id, e.name AS name, n
    ORDER BY n DESC LIMIT 10
    """)
    for r in ck_cands:
        q = f"Why was the {r['name']} configuration option introduced in Redis?"
        b = ask(q)
        if b["status"] == "refused":
            best_refused = (r["name"], "redis.conf", r["n"], q, b)
            print(f"  ✓ REFUSED (ConfigKey): {r['name']!r} ({r['n']} commits)")
            print(f"    question: {q!r}")
            break
        else:
            print(f"  ✗ not refused ({b['status']}): {r['name']!r}")

print()
if best_refused:
    fn, path, commits, q, b = best_refused
    print(f"BEST REFUSAL ENTITY: {fn!r}  path={path}  commits={commits}")
    print(f"QUESTION: {q!r}")
    print(f"STATUS  : {b['status']}")
    print(f"CONF    : {b['confidence']['label']} ({b['confidence']['score']:.2f})")
    print(f"CHANGERS: {[(x.get('author',''), x.get('date','')[:10]) for x in b.get('related',[])[:3]]}")
    print(f"RELATED : {len(b.get('related',[]))}")
else:
    print("WARNING: Could not find a reliable refusal entity")
    fn, path, commits, q = "connectWithMaster", "src/replication.c", 10, \
        "Why does connectWithMaster in replication.c retry connections rather than failing immediately?"

print()
print("=== Final demo table ===")
DEMOS = [
    ("ANSWERED",   "What is the rationale for the Multi-Part AOF mechanism in Redis 7.0?"),
    ("SUPERSEDED", "Why does Redis fail to start by default when a requested bind address is not available?"),
    ("REFUSED",    q if best_refused else "Why does Redis use epoll instead of select on Linux?"),
]
print(f"\n{'Expected':<12} {'Actual':<12} {'Conf':<20} {'Notice':<7} {'History'}")
print("-" * 95)
for expected, dq in DEMOS:
    b = ask(dq)
    actual = b['status']
    conf   = b['confidence']['label']
    score  = b['confidence']['score']
    notice = "YES" if b.get('superseded_notice') else "no"
    hist   = [(h['title'][:35], h['status']) for h in b.get('history', [])[:3]]
    print(f"{expected:<12} {actual:<12} {conf}({score:.2f}){'':6} {notice:<7} {hist}")
