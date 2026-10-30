"""Idempotent loaders (MERGE + UNWIND batches). Run in order: commits -> entities -> threads -> decisions."""
from __future__ import annotations
import hashlib, os
from .db import Neo4jDB
from ..config import settings
from ..llm.provider import embed
from ..models import ExtractedDecision


def _url(sha: str) -> str:
    return f"https://github.com/{settings.repo_owner}/{settings.repo_name}/commit/{sha}"


def load_commits(db: Neo4jDB, commits: list[dict]) -> None:
    rows = [{"sha": c["sha"], "message": c["message"], "date": c["date"], "author": c["author"],
             "person_id": c["email"], "url": _url(c["sha"])} for c in commits]
    db.run_batches("""
    UNWIND $rows AS r
    MERGE (c:Commit {id:r.sha})
      SET c.message=r.message, c.text=r.message, c.date=r.date, c.author=r.author, c.url=r.url
    MERGE (p:Person {id:r.person_id}) SET p.name=r.author
    MERGE (p)-[:AUTHORED]->(c)
    """, rows)


def add_references(db: Neo4jDB, commit_refs: list[dict]) -> None:
    """Create REFERENCES edges from Commit/PullRequest nodes to Issue/PR nodes.

    commit_refs: [{source_id: str, ref_number: int}]
      source_id  — Commit sha OR PR id like "pr:123"
      ref_number — the referenced issue/PR number

    Uses MERGE so re-runs are idempotent.  Only creates Issue/PR stubs if they
    don't already exist (MERGE + SET only sets missing properties).
    """
    if not commit_refs:
        return
    # Commit -> Issue reference
    commit_rows = [r for r in commit_refs if not r["source_id"].startswith("pr:")]
    if commit_rows:
        db.run_batches("""
        UNWIND $rows AS r
        MATCH (c:Commit {id:r.source_id})
        MERGE (target {id:'issue:'+toString(r.ref_number)})
        MERGE (c)-[:REFERENCES]->(target)
        """, commit_rows)
    # PR -> Issue reference  (PR body may reference other issues)
    pr_rows = [r for r in commit_refs if r["source_id"].startswith("pr:")]
    if pr_rows:
        db.run_batches("""
        UNWIND $rows AS r
        MATCH (pr:PullRequest {id:r.source_id})
        MERGE (target {id:'issue:'+toString(r.ref_number)})
        MERGE (pr)-[:REFERENCES]->(target)
        """, pr_rows)


def load_entities(db: Neo4jDB, commit_entities: list[dict]) -> None:
    """commit_entities: [{sha, files:[path], functions:[[path,name]], config_keys:[{key,value,change}]}]"""
    files = [{"sha": c["sha"], "path": p} for c in commit_entities for p in c["files"]]
    db.run_batches("""
    UNWIND $rows AS r
    MATCH (c:Commit {id:r.sha})
    MERGE (f:File {id:r.path}) SET f:Entity, f.path=r.path, f.name=r.path
    MERGE (c)-[:MODIFIES]->(f)
    """, files)
    funcs = [{"sha": c["sha"], "path": p, "name": n} for c in commit_entities for p, n in c["functions"]]
    db.run_batches("""
    UNWIND $rows AS r
    MATCH (c:Commit {id:r.sha})
    MERGE (f:Function {id:'fn:'+r.path+'::'+r.name}) SET f:Entity, f.name=r.name, f.path=r.path
    MERGE (c)-[:MODIFIES]->(f)
    """, funcs)
    keys = [{"sha": c["sha"], "key": k["key"], "value": k["value"], "change": k["change"]}
            for c in commit_entities for k in c["config_keys"]]
    db.run_batches("""
    UNWIND $rows AS r
    MATCH (c:Commit {id:r.sha})
    MERGE (k:ConfigKey {id:'config:'+r.key}) SET k:Entity, k.name=r.key
      SET k.default_value = coalesce(k.default_value, r.value)
    MERGE (c)-[m:MODIFIES]->(k) SET m.change=r.change
    """, keys)


def load_threads(db: Neo4jDB, threads: list[dict], embed_comments: bool = True) -> None:
    prs = [{"id": t["id"], "number": t["number"], "title": t["title"], "url": t["url"],
            "date": t.get("merged_at") or t["created_at"], "author": t["author"],
            "text": f"{t['title']}\n{t['body']}"[:8000], "shas": t["commit_shas"], "closes": t["closes"]}
           for t in threads if t["kind"] == "pr"]
    db.run_batches("""
    UNWIND $rows AS r
    MERGE (pr:PullRequest {id:r.id})
      SET pr.number=r.number, pr.title=r.title, pr.url=r.url, pr.date=r.date, pr.author=r.author, pr.text=r.text
    MERGE (p:Person {id:r.author}) MERGE (p)-[:AUTHORED]->(pr)
    WITH pr, r
    UNWIND r.shas AS sha
    MATCH (c:Commit {id:sha}) MERGE (c)-[:PART_OF]->(pr)
    """, prs)
    db.run_batches("""
    UNWIND $rows AS r
    MATCH (pr:PullRequest {id:r.id})
    UNWIND r.closes AS n
    MERGE (i:Issue {id:'issue:'+toString(n)}) SET i.number=n, i.url=r.url
    MERGE (pr)-[:CLOSES]->(i)
    """, [p for p in prs if p["closes"]])
    comments = []
    for t in threads:
        for c in t["comments"]:
            if (c["body"] or "").strip():
                comments.append({"id": c["id"], "thread": t["id"], "author": c["author"], "date": c["created_at"],
                                 "url": c["url"], "text": c["body"][:4000]})
    if embed_comments and comments:
        for i in range(0, len(comments), 64):
            chunk = comments[i:i + 64]
            for row, v in zip(chunk, embed([c["text"][:1000] for c in chunk])):
                row["embedding"] = v
    db.run_batches("""
    UNWIND $rows AS r
    MATCH (t:PullRequest {id:r.thread})
    MERGE (c:Comment {id:r.id})
      SET c.author=r.author, c.date=r.date, c.url=r.url, c.text=r.text
    FOREACH (_ IN CASE WHEN r.embedding IS NULL THEN [] ELSE [1] END | SET c.embedding=r.embedding)
    MERGE (c)-[:COMMENTED_ON]->(t)
    MERGE (p:Person {id:r.author}) MERGE (p)-[:AUTHORED]->(c)
    """, [cm for cm in comments if cm["thread"].startswith("pr:")])
    db.run_batches("""
    UNWIND $rows AS r
    MATCH (t:Issue {id:r.thread})
    MERGE (c:Comment {id:r.id})
      SET c.author=r.author, c.date=r.date, c.url=r.url, c.text=r.text
    FOREACH (_ IN CASE WHEN r.embedding IS NULL THEN [] ELSE [1] END | SET c.embedding=r.embedding)
    MERGE (c)-[:COMMENTED_ON]->(t)
    MERGE (p:Person {id:r.author}) MERGE (p)-[:AUTHORED]->(c)
    """, [cm for cm in comments if cm["thread"].startswith("issue:")])


def load_documents(db: Neo4jDB, documents: list[dict]) -> None:
    """Load Document evidence nodes (design docs, config comment blocks).

    documents: list of {id, path, section, url, text, source?, start_line?, end_line?}

    Graph structure:
      (Document)-[:DESCRIBES]->(ConfigKey)   when source is redis.conf and section
                                              matches a known ConfigKey id
      (Document)-[:DESCRIBES]->(File)        when source is a .c file; links to the
                                              File node whose id matches the doc's path
      (Document)-[:DESCRIBES]->(Function)    when section resolves to a known Function
                                              (best-effort; skipped if no match)

    Uses MERGE so re-runs are idempotent.
    """
    if not documents:
        return

    # ── 1. MERGE the Document nodes ───────────────────────────────────────────
    rows = [
        {
            "id":      d["id"],
            "path":    d.get("path", ""),
            "section": d.get("section", ""),
            "url":     d.get("url", ""),
            "text":    d.get("text", ""),
            "source":  d.get("source", ""),
            "start":   d.get("start_line", 0),
            "end":     d.get("end_line", 0),
        }
        for d in documents
    ]
    db.run_batches("""
    UNWIND $rows AS r
    MERGE (d:Document {id:r.id})
      SET d.path    = r.path,
          d.section = r.section,
          d.url     = r.url,
          d.text    = r.text,
          d.source  = r.source,
          d.start_line = r.start,
          d.end_line   = r.end
    """, rows)

    # ── 2. Link redis.conf documents to ConfigKey nodes ───────────────────────
    conf_rows = [r for r in rows if r["source"] == "redis.conf" and r["section"]]
    if conf_rows:
        db.run_batches("""
        UNWIND $rows AS r
        MATCH (d:Document {id:r.id})
        MATCH (k:ConfigKey {id:'config:'+r.section})
        MERGE (d)-[:DESCRIBES]->(k)
        """, conf_rows)

    # ── 3. Link C-source documents to File nodes ──────────────────────────────
    c_rows = [r for r in rows if r["source"] not in ("redis.conf", "") and r["path"]]
    if c_rows:
        db.run_batches("""
        UNWIND $rows AS r
        MATCH (d:Document {id:r.id})
        MATCH (f:File {id:r.path})
        MERGE (d)-[:DESCRIBES]->(f)
        """, c_rows)

    # ── 4. Best-effort link to Function nodes (section name = function name) ──
    fn_rows = [r for r in c_rows if r["section"] and r["section"] != "unknown"]
    if fn_rows:
        db.run_batches("""
        UNWIND $rows AS r
        MATCH (d:Document {id:r.id})
        MATCH (fn:Function)
          WHERE fn.name = r.section AND fn.path = r.path
        MERGE (d)-[:DESCRIBES]->(fn)
        """, fn_rows)


def decision_id(d: ExtractedDecision) -> str:
    return hashlib.sha1(f"{d.thread_id}|{d.title}".encode()).hexdigest()[:16]


def load_decisions_from_documents(
    db: Neo4jDB,
    decisions: list[ExtractedDecision],
) -> dict:
    """Variant of load_decisions specialised for Document-sourced decisions.

    Key differences from load_decisions:
    - EVIDENCED_BY always points to the Document node (id = doc.id = path#Lstart).
    - GOVERNS fallback: uses the Document's DESCRIBES targets, preferring
      ConfigKey/Function over File nodes (File is the last resort).
    - Returns stats dict: {loaded, zero_governs, file_only_governs}.
    """
    import logging
    log = logging.getLogger(__name__)

    if not decisions:
        return {"loaded": 0, "zero_governs": 0, "file_only_governs": 0}

    embs = embed([f"{d.title}. {d.summary}" for d in decisions])
    rows = []
    for d, e in zip(decisions, embs):
        rows.append({
            "id":         decision_id(d),
            "title":      d.title,
            "summary":    d.summary,
            "rationale":  d.rationale,
            "alts":       d.alternatives_rejected,
            "date":       d.decided_on if d.decided_on else None,   # never store ""
            "explicit":   d.explicit_rationale,
            "agreement":  d.agreement,
            "embedding":  e,
            "doc_id":     d.thread_id,   # the Document node id  (path#Lstart)
            "governs":    d.governs,
            "by":         d.decided_by,
            "spans":      [{"source": s.source_id, "quote": s.quote} for s in d.spans],
        })

    # 1. MERGE Decision nodes
    db.run_batches("""
    UNWIND $rows AS r
    MERGE (d:Decision {id:r.id})
      SET d.title=r.title, d.summary=r.summary, d.rationale=r.rationale,
          d.alternatives_rejected=r.alts,
          d.decided_on=r.date,
          d.explicit_rationale=r.explicit, d.agreement=r.agreement,
          d.embedding=r.embedding, d.status=coalesce(d.status,'ACTIVE'),
          d.source_kind='document'
    """, rows)

    # 2. EVIDENCED_BY -> Document node (primary evidence)
    db.run_batches("""
    UNWIND $rows AS r
    MATCH (d:Decision {id:r.id})
    MATCH (doc:Document {id:r.doc_id})
    MERGE (d)-[:EVIDENCED_BY]->(doc)
    """, rows)

    # 3. Spans -> other Document/entity nodes
    db.run_batches("""
    UNWIND $rows AS r
    MATCH (d:Decision {id:r.id})
    UNWIND r.spans AS s
    MATCH (e {id:s.source})
    WHERE e:Document OR e:Comment OR e:PullRequest OR e:Commit
    MERGE (d)-[ev:EVIDENCED_BY]->(e) SET ev.quote=s.quote
    """, rows)

    # 4. GOVERNS — explicit hints from the LLM first
    db.run_batches("""
    UNWIND $rows AS r
    MATCH (d:Decision {id:r.id})
    UNWIND r.governs AS g
    MATCH (e:Entity) WHERE toLower(e.name)=toLower(g) OR toLower(e.path)=toLower(g)
    MERGE (d)-[:GOVERNS]->(e)
    """, rows)

    # 5. GOVERNS fallback — use DESCRIBES targets of the Document,
    #    preferring ConfigKey/Function over File
    db.run_batches("""
    UNWIND $rows AS r
    MATCH (d:Decision {id:r.id})
    WHERE NOT (d)-[:GOVERNS]->(:Entity)
    MATCH (doc:Document {id:r.doc_id})-[:DESCRIBES]->(t)
    WHERE t:ConfigKey OR t:Function
    MERGE (d)-[:GOVERNS]->(t)
    """, rows)

    # File fallback only when no ConfigKey/Function link exists — mark coarse
    db.run_batches("""
    UNWIND $rows AS r
    MATCH (d:Decision {id:r.id})
    WHERE NOT (d)-[:GOVERNS]->(:ConfigKey) AND NOT (d)-[:GOVERNS]->(:Function)
    MATCH (doc:Document {id:r.doc_id})-[:DESCRIBES]->(f:File)
    MERGE (d)-[g:GOVERNS]->(f)
    SET g.link_quality = 'coarse'
    """, rows)

    # 6. MADE_BY
    db.run_batches("""
    UNWIND $rows AS r
    MATCH (d:Decision {id:r.id})
    UNWIND r.by AS login
    MERGE (p:Person {id:login}) MERGE (d)-[:MADE_BY]->(p)
    """, [r for r in rows if r.get("by")])

    # 7. Collect stats
    ids = [r["id"] for r in rows]
    zero_governs_rows = db.run("""
    UNWIND $ids AS did
    MATCH (d:Decision {id:did})
    WHERE NOT (d)-[:GOVERNS]->(:Entity)
    RETURN d.id AS id, d.title AS title
    """, ids=ids)
    for o in zero_governs_rows:
        log.warning("Doc-Decision %s (%s) has no GOVERNS links", o["id"], o["title"][:60])

    file_only_rows = db.run("""
    UNWIND $ids AS did
    MATCH (d:Decision {id:did})
    WHERE (d)-[:GOVERNS]->(:File)
      AND NOT (d)-[:GOVERNS]->(:ConfigKey)
      AND NOT (d)-[:GOVERNS]->(:Function)
    RETURN count(d) AS n
    """, ids=ids)

    return {
        "loaded":           len(rows),
        "zero_governs":     len(zero_governs_rows),
        "file_only_governs": (file_only_rows[0]["n"] if file_only_rows else 0),
    }


def load_decisions(db: Neo4jDB, decisions: list[ExtractedDecision]) -> None:
    import logging
    log = logging.getLogger(__name__)

    if not decisions:
        return
    embs = embed([f"{d.title}. {d.summary}" for d in decisions])
    rows = []
    for d, e in zip(decisions, embs):
        rows.append({"id": decision_id(d), "title": d.title, "summary": d.summary, "rationale": d.rationale,
                     "alts": d.alternatives_rejected, "date": d.decided_on if d.decided_on else None,
                     "explicit": d.explicit_rationale,
                     "agreement": d.agreement, "embedding": e, "thread": d.thread_id,
                     "governs": d.governs, "by": d.decided_by,
                     "spans": [{"source": s.source_id, "quote": s.quote} for s in d.spans]})
    db.run_batches("""
    UNWIND $rows AS r
    MERGE (d:Decision {id:r.id})
      SET d.title=r.title, d.summary=r.summary, d.rationale=r.rationale, d.alternatives_rejected=r.alts,
          d.decided_on=r.date, d.explicit_rationale=r.explicit, d.agreement=r.agreement,
          d.embedding=r.embedding, d.status=coalesce(d.status,'ACTIVE')
    WITH d, r
    MATCH (t {id:r.thread}) MERGE (d)-[:EVIDENCED_BY]->(t)
    """, rows)
    db.run_batches("""
    UNWIND $rows AS r
    MATCH (d:Decision {id:r.id})
    UNWIND r.spans AS s
    MATCH (e {id:s.source})
    WHERE e:Comment OR e:PullRequest OR e:Issue OR e:Commit OR e:Document
    MERGE (d)-[ev:EVIDENCED_BY]->(e) SET ev.quote=s.quote
    """, rows)
    db.run_batches("""
    UNWIND $rows AS r
    MATCH (d:Decision {id:r.id})
    UNWIND r.governs AS g
    MATCH (e:Entity) WHERE toLower(e.name)=toLower(g) OR toLower(e.path)=toLower(g)
    MERGE (d)-[:GOVERNS]->(e)
    """, rows)
    # fallback: entities touched by the thread's commits and named in the decision text
    # For PR threads: Commit-[:PART_OF]->PullRequest; for bare commit threads: use Commit directly.
    # Use two separate queries (one for PR threads, one for bare commit threads) to avoid
    # the deprecated CALL {} subquery syntax warning in Neo4j 5.27+.
    pr_thread_rows = [r for r in rows if not r["thread"].startswith("sha:") and ":" in r["thread"]]
    commit_thread_rows = [r for r in rows if not (":" in r["thread"] and not r["thread"].startswith("commit:"))]
    # Simpler: split by thread id prefix
    pr_rows_governs = [r for r in rows if r["thread"].startswith("pr:")]
    commit_rows_governs = [r for r in rows if not r["thread"].startswith("pr:")]

    if pr_rows_governs:
        db.run_batches("""
        UNWIND $rows AS r
        MATCH (d:Decision {id:r.id}) WHERE NOT (d)-[:GOVERNS]->(:Entity)
        MATCH (c:Commit)-[:PART_OF]->(t:PullRequest {id:r.thread})
        MATCH (c)-[:MODIFIES]->(e:Entity)
        WHERE size(e.name) > 3 AND toLower(d.title+' '+d.summary+' '+d.rationale) CONTAINS toLower(e.name)
        MERGE (d)-[:GOVERNS]->(e)
        """, pr_rows_governs)

    if commit_rows_governs:
        db.run_batches("""
        UNWIND $rows AS r
        MATCH (d:Decision {id:r.id}) WHERE NOT (d)-[:GOVERNS]->(:Entity)
        MATCH (c:Commit {id:r.thread})
        WHERE (d)-[:EVIDENCED_BY]->(c)
        MATCH (c)-[:MODIFIES]->(e:Entity)
        WHERE size(e.name) > 3 AND toLower(d.title+' '+d.summary+' '+d.rationale) CONTAINS toLower(e.name)
        MERGE (d)-[:GOVERNS]->(e)
        """, commit_rows_governs)

    # Log decisions with zero GOVERNS links — they are unreachable by entity search
    orphan_rows = db.run("""
    UNWIND $ids AS did
    MATCH (d:Decision {id:did})
    WHERE NOT (d)-[:GOVERNS]->(:Entity)
    RETURN d.id AS id, d.title AS title
    """, ids=[r["id"] for r in rows])
    if orphan_rows:
        for o in orphan_rows:
            log.warning("Decision %s (%s) has no GOVERNS links — unreachable by entity search", o["id"], o["title"][:60])
    db.run_batches("""
    UNWIND $rows AS r
    MATCH (d:Decision {id:r.id})
    UNWIND r.by AS login
    MERGE (p:Person {id:login}) MERGE (d)-[:MADE_BY]->(p)
    """, rows)
