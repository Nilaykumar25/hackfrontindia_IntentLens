"""
fix_pass_probes.py — Items 3, 4, 5, 6, 7 from the fix pass.
Run with: .venv\Scripts\python.exe -m scripts.fix_pass_probes
"""
import sys, json, re
sys.path.insert(0, '.')
import httpx
from backend.app.graph.db import get_db

BASE = "http://127.0.0.1:8000"
db   = get_db()

def ask(q):
    r = httpx.post(f"{BASE}/ask", json={"question": q}, timeout=90)
    return r.json()

# ─────────────────────────────────────────────────────────────────────────────
# ITEM 3: Bind question — print full answer text and check both facts
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 70)
print("ITEM 3: Bind-address demo question — full answer audit")
print("=" * 70)

b = ask("Why does Redis ignore EADDRNOTAVAIL errors for bind addresses with a '-' prefix?")
print(f"\nstatus      : {b['status']}")
print(f"confidence  : {b['confidence']['label']} ({b['confidence']['score']:.2f})")
print(f"sup_notice  : {(b.get('superseded_notice') or '')[:120]}")
print(f"\nFULL ANSWER :\n{b.get('answer','')}")
print(f"\nDECISION    : {b.get('decision',{}).get('title','')}")
print(f"HISTORY     : {[(h['title'][:50], h['status']) for h in b.get('history',[])]}")
print(f"\nEVIDENCE PACK:")
for e in b.get('evidence', []):
    print(f"  [{e['ref']}] {e['kind']} {e.get('date','')[:10]}  quote: {(e.get('quote') or e.get('snippet',''))[:80]!r}")

# Check if the answer contains BOTH facts
answer_text = (b.get('answer') or '').lower()
has_ignore   = "ignore" in answer_text or "prefix" in answer_text or "eaddrnotavail" in answer_text or "'-'" in answer_text
has_faildefault = "fail" in answer_text or "default" in answer_text or "unavailable" in answer_text

print(f"\nFact check:")
print(f"  Has '-' prefix / ignore behaviour: {has_ignore}")
print(f"  Has 'fail by default' behaviour   : {has_faildefault}")

if not (has_ignore and has_faildefault):
    print("\n  ⚠ Answer is MISSING one of the two facts.")
    print("  → Will try the alternative question formulation.")
    b2 = ask("Why does Redis fail to start by default when a requested bind address is not available?")
    print(f"\n  ALT status : {b2['status']}  conf={b2['confidence']['label']} ({b2['confidence']['score']:.2f})")
    print(f"  ALT notice : {(b2.get('superseded_notice') or '')[:120]}")
    print(f"  ALT answer : {(b2.get('answer') or '')[:300]}")
    print(f"  ALT history: {[(h['title'][:50], h['status']) for h in b2.get('history',[])]}")

# ─────────────────────────────────────────────────────────────────────────────
# ITEM 4: Find an entity with commits but NO Decision — for the refusal demo
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("ITEM 4: Find in-scope entity with ≥3 commits and NO governing Decision")
print("=" * 70)

# Cypher to find it
rows = db.run("""
MATCH (e:Entity)<-[:MODIFIES]-(c:Commit)
WHERE (e:File OR e:Function OR e:ConfigKey)
  AND e.id STARTS WITH 'src/'
  AND NOT EXISTS { MATCH (d:Decision)-[:GOVERNS]->(e) }
WITH e, count(c) AS commit_count
WHERE commit_count >= 3
RETURN e.id AS id, e.name AS name, labels(e)[0] AS lbl, commit_count
ORDER BY commit_count DESC
LIMIT 10
""")
print("Cypher used:")
print("""  MATCH (e:Entity)<-[:MODIFIES]-(c:Commit)
  WHERE (e:File OR e:Function OR e:ConfigKey)
    AND e.id STARTS WITH 'src/'
    AND NOT EXISTS { MATCH (d:Decision)-[:GOVERNS]->(e) }
  WITH e, count(c) AS commit_count
  WHERE commit_count >= 3
  RETURN e.id, e.name, labels(e)[0], commit_count ORDER BY commit_count DESC LIMIT 10""")
print()
for r in rows:
    print(f"  {r['lbl']:<12} commits={r['commit_count']:3d}  {r['id']}")

# Also try redis.conf keys
rows2 = db.run("""
MATCH (e:ConfigKey)<-[:MODIFIES]-(c:Commit)
  AND NOT EXISTS { MATCH (d:Decision)-[:GOVERNS]->(e) }
WITH e, count(c) AS commit_count
WHERE commit_count >= 3
RETURN e.id AS id, e.name AS name, commit_count
ORDER BY commit_count DESC LIMIT 5
""")

# Simpler query for ConfigKey
rows2 = db.run("""
MATCH (e:ConfigKey)<-[:MODIFIES]-(c:Commit)
WHERE NOT EXISTS { MATCH (d:Decision)-[:GOVERNS]->(e) }
WITH e, count(c) AS commit_count
WHERE commit_count >= 3
RETURN e.id AS id, e.name AS name, commit_count
ORDER BY commit_count DESC LIMIT 5
""")
print("\nConfig keys with no decision:")
for r in rows2:
    print(f"  ConfigKey  commits={r['commit_count']:3d}  {r['id']}")

# Pick first File/Function entity and build a natural "why" question
best = rows[0] if rows else None
if best:
    print(f"\nChosen entity: {best['lbl']} {best['id']!r}  ({best['commit_count']} commits)")

    # Get some commit context for a natural question
    commits = db.run("""
    MATCH (e:Entity {id:$eid})<-[:MODIFIES]-(c:Commit)
    RETURN c.message AS msg ORDER BY c.date DESC LIMIT 3
    """, eid=best["id"])
    for c in commits:
        print(f"  commit: {c['msg'][:80]!r}")

    # Build the question
    fn_name = best["name"]
    natural_q = f"Why does the function {fn_name} exist and what is it responsible for?"
    print(f"\nNatural question: {natural_q!r}")

    r_refused = ask(natural_q)
    print(f"\nAPI result:")
    print(f"  status     : {r_refused['status']}")
    print(f"  confidence : {r_refused['confidence']['label']} ({r_refused['confidence']['score']:.2f})")
    print(f"  changers   : {[(x.get('author','?'), x.get('date','?')[:10]) for x in r_refused.get('related',[])[:3]]}")

# ─────────────────────────────────────────────────────────────────────────────
# ITEM 5: Review flags — supersession edges to flag
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("ITEM 5: Review flags — edges 42, 51, 52, 57, 32, 33")
print("=" * 70)

# Fetch all edges ordered by table position to identify by line number
edges = db.run("""
MATCH (n:Decision)-[r:SUPERSEDES|REFINES]->(o:Decision)
RETURN n.id AS nid, o.id AS oid, type(r) AS rtype,
       n.title AS newer_title, o.title AS older_title,
       r.confidence AS conf, coalesce(r.review_flag,'') AS rf
ORDER BY rtype DESC, r.confidence DESC
""")

print(f"Total edges: {len(edges)}")
already_flagged = sum(1 for e in edges if e['rf'] == 'needs_review')
print(f"Already flagged: {already_flagged}")

# The spec references links 42, 51, 52, 57, 32, 33 from supersession_found.md
# Those are line numbers in the markdown detail section (### [N])
# We flag by matching titles in those link entries
EXTRA_FLAG_PATTERNS = [
    # Link 32: "Remove temporary rdb file" REFINES "Avoid snprintf"
    ("Remove temporary rdb file in background", "Avoid snprintf"),
    # Link 33: "Update fsynced_reploff_pending" REFINES "Check AOF_FSYNC_ALWAYS"
    ("Update fsynced_reploff_pending", "Check AOF_FSYNC_ALWAYS"),
    # Link 42: "UINT opcode for backwards compatibility" (already flagged)
    ("UINT opcode for backwards compatibility", ""),
    # Link 51: "Track config-load depth" — same day, TLS admin change
    ("Track config-load depth", "Log parent-domain advisory"),
    # Link 52: "Deduplicate parent-domain advisory" — same day
    ("Deduplicate parent-domain advisory", "Track config-load depth"),
    # Link 57: "Add listpack encoding for list" (same day pair) REFINES another
    ("Add listpack encoding for list", "Add listpack encoding for list"),
]

flagged_now = 0
for newer_pat, older_pat in EXTRA_FLAG_PATTERNS:
    for e in edges:
        if e['rf'] == 'needs_review':
            continue
        if newer_pat.lower() in e['newer_title'].lower():
            if not older_pat or older_pat.lower() in e['older_title'].lower():
                db.run("""
                MATCH (n:Decision {id:$nid})-[r:SUPERSEDES|REFINES]->(o:Decision {id:$oid})
                SET r.review_flag = 'needs_review'
                """, nid=e['nid'], oid=e['oid'])
                flagged_now += 1
                print(f"  FLAGGED [{e['rtype']}] {e['newer_title'][:55]!r}")
                print(f"          -> {e['older_title'][:55]!r}")

# Re-count
final_flagged = db.run("""
MATCH ()-[r:SUPERSEDES|REFINES]->()
WHERE r.review_flag = 'needs_review'
RETURN count(r) AS n
""")[0]["n"]
print(f"\nTotal needs_review after this pass: {final_flagged}")

# ─────────────────────────────────────────────────────────────────────────────
# ITEM 6: Document nodes without source_kind — provenance and exclusion
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("ITEM 6: Document nodes without source_kind")
print("=" * 70)

count = db.run("""
MATCH (d:Document)
WHERE d.source_kind IS NULL OR d.source_kind = ''
RETURN count(d) AS n
""")[0]["n"]
print(f"Documents without source_kind: {count}")

# Sample 3 examples
examples = db.run("""
MATCH (d:Document)
WHERE d.source_kind IS NULL OR d.source_kind = ''
RETURN d.id AS id, d.path AS path, d.section AS section,
       left(d.text, 150) AS text_preview
LIMIT 3
""")
print("\n3 examples:")
for ex in examples:
    print(f"  id      : {ex['id']}")
    print(f"  path    : {ex['path']}")
    print(f"  section : {ex['section']}")
    print(f"  text    : {ex['text_preview']!r}")
    print()

# Categorise by path
path_summary = db.run("""
MATCH (d:Document)
WHERE d.source_kind IS NULL OR d.source_kind = ''
WITH d.path AS path, count(d) AS n
ORDER BY n DESC LIMIT 15
RETURN path, n
""")
print("Path distribution (top 15):")
for r in path_summary:
    print(f"  {r['n']:4d}  {r['path']}")

# Tag all without source_kind as "other"
db.run("""
MATCH (d:Document)
WHERE d.source_kind IS NULL OR d.source_kind = ''
SET d.source_kind = 'other'
""")
tagged = db.run("""
MATCH (d:Document {source_kind:'other'}) RETURN count(d) AS n
""")[0]["n"]
print(f"\nTagged {tagged} documents as source_kind='other'")

# ─────────────────────────────────────────────────────────────────────────────
# ITEM 7: Re-run three demo questions
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("ITEM 7: Re-run three demo questions")
print("=" * 70)

DEMO = [
    ("ANSWERED",   "What is the rationale for the Multi-Part AOF mechanism in Redis 7.0?"),
    ("SUPERSEDED", "Why does Redis ignore EADDRNOTAVAIL errors for bind addresses with a '-' prefix?"),
    ("REFUSED",    "Why does Redis use epoll instead of select on Linux?"),
]

print(f"\n{'#':<3} {'Expected':<12} {'Actual':<12} {'Conf':<18} {'Notice':<6} {'History'}")
print("-" * 80)
for expected, q in DEMO:
    b = ask(q)
    actual   = b['status']
    conf_lbl = b['confidence']['label']
    score    = b['confidence']['score']
    notice   = "YES" if b.get('superseded_notice') else "no"
    hist     = [(h['title'][:30], h['status']) for h in b.get('history', [])[:3]]
    print(f"  {expected:<12} {actual:<12} {conf_lbl}({score:.2f}){'':4} notice={notice}  history={hist}")
