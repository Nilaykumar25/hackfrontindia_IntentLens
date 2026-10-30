"""Items 4-7: find refusal entity, flag edges, tag docs, final demo table."""
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
# ITEM 4: Function entity with commits but no Decision
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 70)
print("ITEM 4: Function entities with ≥3 commits, no Decision")
print("=" * 70)

# Split the NOT EXISTS from the main WHERE to avoid Cypher 5 syntax issue
rows = db.run("""
MATCH (e:Function)<-[:MODIFIES]-(c:Commit)
WITH e, count(c) AS commit_count
WHERE commit_count >= 5
  AND NOT EXISTS { MATCH (d:Decision)-[:GOVERNS]->(e) }
RETURN e.id AS id, e.name AS name, e.path AS path, commit_count
ORDER BY commit_count DESC
LIMIT 10
""")
print("Function entities (no Decision, ≥5 commits):")
for r in rows:
    print(f"  commits={r['commit_count']:3d}  {r['name']:<35}  {r['path']}")

best = rows[0] if rows else None
if best:
    fn_name  = best["name"]
    fn_path  = best["path"] or ""
    file_base = fn_path.split("/")[-1] if fn_path else "replication.c"
    question = f"Why does {fn_name} in {file_base} use its current approach?"
    print(f"\nChosen: {fn_name!r} from {fn_path}")
    print(f"Question: {question!r}")
    b = ask(question)
    status = b['status']
    conf   = b['confidence']['label']
    score  = b['confidence']['score']
    changers = [(x.get('author','?'), x.get('date','?')[:10]) for x in b.get('related',[])[:3]]
    print(f"\nAPI result: status={status}  conf={conf}({score:.2f})")
    print(f"  last_changers={changers}")
    if status == 'refused':
        print("  ✓ REFUSED as expected")
    else:
        print(f"  ✗ NOT refused — answer={b.get('answer','')[:120]}")
        # Try with a different phrasing
        question2 = f"What is the design rationale behind the {fn_name} function in Redis?"
        b2 = ask(question2)
        print(f"\n  Retry with: {question2!r}")
        print(f"  status={b2['status']}  conf={b2['confidence']['label']}({b2['confidence']['score']:.2f})")
        if b2['status'] == 'refused':
            question = question2
            b = b2

# ─────────────────────────────────────────────────────────────────────────────
# ITEM 5: Review flags — additional edges 32, 33, 51, 52, 57
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("ITEM 5: Flag additional review edges")
print("=" * 70)

edges = db.run("""
MATCH (n:Decision)-[r:SUPERSEDES|REFINES]->(o:Decision)
RETURN n.id AS nid, o.id AS oid, type(r) AS rtype,
       n.title AS newer_title, o.title AS older_title,
       n.decided_on AS newer_date, o.decided_on AS older_date,
       r.confidence AS conf, coalesce(r.review_flag,'') AS rf
ORDER BY rtype DESC, r.confidence DESC
""")

already = sum(1 for e in edges if e['rf'] == 'needs_review')
print(f"Already flagged: {already}/{len(edges)}")

# Flag by title pattern + same-day condition
EXTRA_PATTERNS = [
    # Link 32: "Remove temporary rdb file in background" REFINES "Avoid snprintf in rdbRemoveTempFile"
    ("Remove temporary rdb file in background", "Avoid snprintf"),
    # Link 33: "Update fsynced_reploff_pending" REFINES "Check AOF_FSYNC_ALWAYS in flushAppendOnlyFile"
    ("Update fsynced_reploff_pending", "Check AOF_FSYNC_ALWAYS"),
    # Link 57: same-day duplicate "Add listpack encoding for list" -> "Add listpack encoding for list"
    ("Add listpack encoding for list", "Add listpack encoding for list"),
]
# Also flag same-day pairs (dates match exactly) that are REFINES — these are very likely cosmetic
SAME_DAY_REFINES = [(e['nid'], e['oid']) for e in edges
                    if e['rtype'] == 'REFINES'
                    and e['rf'] != 'needs_review'
                    and e.get('newer_date') and e.get('older_date')
                    and str(e['newer_date'])[:10] == str(e['older_date'])[:10]]

newly = 0
for nid, oid in SAME_DAY_REFINES:
    e = next((x for x in edges if x['nid'] == nid and x['oid'] == oid), None)
    if not e: continue
    db.run("""
    MATCH (n:Decision {id:$nid})-[r:REFINES]->(o:Decision {id:$oid})
    SET r.review_flag = 'needs_review'
    """, nid=nid, oid=oid)
    newly += 1
    print(f"  FLAGGED (same-day) [{e['rtype']}] {e['newer_title'][:50]!r}")

for newer_pat, older_pat in EXTRA_PATTERNS:
    for e in edges:
        if e['rf'] == 'needs_review': continue
        if newer_pat.lower() in e['newer_title'].lower():
            if not older_pat or older_pat.lower() in e['older_title'].lower():
                db.run("""
                MATCH (n:Decision {id:$nid})-[r:SUPERSEDES|REFINES]->(o:Decision {id:$oid})
                SET r.review_flag = 'needs_review'
                """, nid=e['nid'], oid=e['oid'])
                newly += 1
                print(f"  FLAGGED [{e['rtype']}] {e['newer_title'][:55]!r}")

total_flagged = db.run("""
MATCH ()-[r:SUPERSEDES|REFINES]->()
WHERE r.review_flag = 'needs_review'
RETURN count(r) AS n
""")[0]["n"]
print(f"\nNewly flagged this run: {newly}")
print(f"Total needs_review: {total_flagged}")
print()
# List all flagged edges
flagged_edges = db.run("""
MATCH (n:Decision)-[r:SUPERSEDES|REFINES]->(o:Decision)
WHERE r.review_flag = 'needs_review'
RETURN n.title AS nt, o.title AS ot, type(r) AS rt, r.confidence AS conf
ORDER BY rt DESC, r.confidence DESC
""")
print("All flagged edges:")
for i, e in enumerate(flagged_edges, 1):
    print(f"  [{i}] [{e['rt']}] conf={e['conf']:.2f}")
    print(f"       NEWER: {e['nt'][:65]}")
    print(f"       OLDER: {e['ot'][:65]}")

# ─────────────────────────────────────────────────────────────────────────────
# ITEM 6: Verify doc tagging and report
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("ITEM 6: Document source_kind distribution")
print("=" * 70)

sk_rows = db.run("""
MATCH (d:Document)
RETURN coalesce(d.source_kind,'(none)') AS sk, count(d) AS n
ORDER BY n DESC
""")
for r in sk_rows:
    print(f"  {r['sk']:<30} {r['n']}")

# ─────────────────────────────────────────────────────────────────────────────
# ITEM 7: Final three demo questions
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("ITEM 7: Three demo questions — final table")
print("=" * 70)

# Q1 ANSWERED
q1 = "What is the rationale for the Multi-Part AOF mechanism in Redis 7.0?"
# Q2 SUPERSEDED — use the alt that clearly mentions fail-to-start
q2 = "Why does Redis fail to start by default when a requested bind address is not available?"
# Q3 REFUSED
q3 = "Why does Redis use epoll instead of select on Linux?"

DEMOS = [
    ("ANSWERED",   q1),
    ("SUPERSEDED", q2),
    ("REFUSED",    q3),
]

print(f"\n{'Expected':<12} {'Actual':<12} {'Conf':<20} {'Notice':<6} {'History items'}")
print("-" * 90)
results = []
for expected, q in DEMOS:
    b = ask(q)
    actual   = b['status']
    conf_lbl = b['confidence']['label']
    score    = b['confidence']['score']
    notice   = "YES" if b.get('superseded_notice') else "no"
    hist_items = [(h['title'][:35], h['status']) for h in b.get('history', [])[:3]]
    results.append((expected, q, actual, conf_lbl, score, notice, hist_items))
    print(f"{expected:<12} {actual:<12} {conf_lbl}({score:.2f}){'':6} {notice:<6} {hist_items}")

print("\nFull supersession notice for Q2:")
b2 = ask(q2)
print(f"  {b2.get('superseded_notice','')}")
print(f"\nHistory for Q2:")
for h in b2.get('history', []):
    print(f"  [{h['status']}] {h['title']}")
