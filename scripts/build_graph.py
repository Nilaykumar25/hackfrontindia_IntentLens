"""Load cache into Neo4j and mine decisions. Usage: python -m scripts.build_graph [--limit 50] [--skip-mining] [--docs-only]"""
import argparse, json, os
from tqdm import tqdm

from backend.app.config import settings
from backend.app.extraction.decision_miner import mine_thread, mine_document
from backend.app.extraction.entities import (
    entity_ids_for_commit, find_refs, parse_config_keys,
)
from backend.app.graph import loader
from backend.app.graph.db import get_db
from backend.app.llm.provider import get_llm
from backend.app.models import Comment, Thread


def read_jsonl(name: str) -> list[dict]:
    p = os.path.join(settings.cache_dir, name)
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if os.path.exists(p) else []


def doc_to_thread(d: dict) -> Thread:
    """Convert a kept source-tagged Document record into a Thread for mining."""
    return Thread(
        id=d["id"],              # path#Lstart  — matches the Document node id
        kind="document",
        title=d.get("section") or d.get("path", ""),
        body=d.get("text", ""),
        url=d.get("url", ""),
        author="",
        created_at="",
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="mine only the first N threads (sample run)")
    ap.add_argument("--skip-mining", action="store_true")
    ap.add_argument("--docs-only", action="store_true",
                    help="mine only kept Document threads (skip PR/commit mining)")
    args = ap.parse_args()
    db = get_db()
    commits, pr_threads = read_jsonl("commits.jsonl"), read_jsonl("threads.jsonl")

    known = set()
    for cf in [p for p in settings.paths if p.endswith(".conf")]:
        path = os.path.join(settings.repo_local_path, cf)
        if os.path.exists(path):
            known |= set(parse_config_keys(open(path, encoding="utf-8", errors="ignore").read()))

    if not args.docs_only:
        print("loading commits:", len(commits))
        loader.load_commits(db, commits)
        ents = []
        for c in commits:
            e = entity_ids_for_commit(c["files"], {p for p in settings.paths if p.endswith(".conf")}, known or None)
            ents.append({"sha": c["sha"], **e})
        loader.load_entities(db, ents)
        print("loading threads:", len(pr_threads))
        loader.load_threads(db, pr_threads)

        # Task 8: REFERENCES edges — commits and PRs referencing issues/PRs
        commit_refs = [
            {"source_id": c["sha"], "ref_number": n}
            for c in commits
            for n in find_refs(c["message"])
        ]
        pr_refs = [
            {"source_id": t["id"], "ref_number": n}
            for t in pr_threads
            for n in find_refs(t.get("body", "") + " " + t.get("title", ""))
        ]
        all_refs = commit_refs + pr_refs
        if all_refs:
            print(f"loading references: {len(all_refs)} (commits={len(commit_refs)}, prs={len(pr_refs)})")
            loader.add_references(db, all_refs)

    # load documents (design docs + config comment blocks)
    # Run ingest_docs first so documents.jsonl is up to date
    import subprocess, sys as _sys
    _ingest = subprocess.run(
        [_sys.executable, "scripts/ingest_docs.py"],
        capture_output=True, text=True,
    )
    if _ingest.returncode != 0:
        print("ingest_docs.py error:", _ingest.stderr, file=__import__("sys").stderr)
    else:
        print(_ingest.stdout.strip())

    docs = read_jsonl("documents.jsonl")
    if docs:
        # Separate our new source-tagged docs from legacy chunk docs
        source_docs = [d for d in docs if d.get("source") or d.get("start_line")]
        other_docs  = [d for d in docs if not (d.get("source") or d.get("start_line"))]
        print(f"loading documents: {len(docs)} total "
              f"({len(source_docs)} source-tagged, {len(other_docs)} legacy)")
        loader.load_documents(db, docs)
    else:
        print("no documents.jsonl found")

    # substantial standalone commits become commit-threads (many projects commit directly)
    in_pr = {s for t in pr_threads for s in t["commit_shas"]}
    commit_threads = [Thread(id=f"commit:{c['sha']}", kind="commit", title=c["message"].split("\n")[0], body=c["message"],
                             url=f"https://github.com/{settings.repo_owner}/{settings.repo_name}/commit/{c['sha']}",
                             author=c["author"], created_at=c["date"], commit_shas=[c["sha"]],
                             files=[f["path"] for f in c["files"]]).model_dump()
                      for c in commits if c["sha"] not in in_pr and len(c["message"]) > 300]

    if args.skip_mining:
        return

    # ── Document thread mining ───────────────────────────────────────────────
    kept_docs = [d for d in docs if d.get("source_kind") == "source_comment"]
    doc_threads = [doc_to_thread(d) for d in kept_docs]
    print(f"document threads available for mining: {len(doc_threads)}")

    # ── build work list ──────────────────────────────────────────────────────
    if args.docs_only:
        work = doc_threads
    else:
        work = [Thread(**t) for t in pr_threads] + [Thread(**t) for t in commit_threads] + doc_threads

    if args.limit:
        # When --limit is set with --docs-only, sample from doc_threads;
        # otherwise sample from the beginning (PRs first) as before.
        if args.docs_only:
            import random; random.seed(0)
            work = random.sample(work, min(args.limit, len(work)))
        else:
            work = work[: args.limit]

    llm = get_llm()
    decisions_pr_commit = []
    decisions_doc       = []
    doc_decision_counts: dict[str, int] = {}  # doc_id -> count

    for t in tqdm(work, desc="mining"):
        try:
            mined = mine_document(llm, t) if t.kind == "document" else mine_thread(llm, t)
        except Exception as ex:
            print("skip", t.id, ex)
            continue

        if t.kind == "document":
            decisions_doc.extend(mined)
            doc_decision_counts[t.id] = len(mined)
        else:
            decisions_pr_commit.extend(mined)

    # PR/commit decisions — existing path
    if decisions_pr_commit:
        for d in decisions_pr_commit:
            if d.thread_id.startswith("commit:"):
                d.thread_id = d.thread_id.split(":", 1)[1]
        loader.load_decisions(db, decisions_pr_commit)
        print(f"decisions loaded (PR/commit): {len(decisions_pr_commit)}")

    # Document decisions — specialised loader
    if decisions_doc:
        stats = loader.load_decisions_from_documents(db, decisions_doc)
        print(f"decisions loaded (documents): {stats['loaded']}")
        print(f"  zero GOVERNS links        : {stats['zero_governs']}")
        print(f"  File-only GOVERNS         : {stats['file_only_governs']}")

        # Per-document counts
        print("\nDecisions per document (non-zero only):")
        for doc_id, n in sorted(doc_decision_counts.items(), key=lambda x: -x[1]):
            if n > 0:
                print(f"  {n:3d}  {doc_id}")

    print(f"\nTotal decisions: {len(decisions_pr_commit) + len(decisions_doc)}")


if __name__ == "__main__":
    main()
