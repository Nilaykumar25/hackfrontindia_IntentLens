"""CLI for asking IntentLens a question and printing the full response.

Usage:
    python -m scripts.ask_cli "Why is repl-backlog-size 1mb?"
    python -m scripts.ask_cli "Why is repl-backlog-size 1mb?" --lang en
    python -m scripts.ask_cli "What is the meaning of life?" --timing

Prints the full AnswerResponse as formatted JSON.
With --timing, also prints per-stage wall-clock times.
"""
from __future__ import annotations

import argparse
import json
import sys
import time


def main() -> None:
    ap = argparse.ArgumentParser(description="Ask IntentLens a question")
    ap.add_argument("question", help="The question to ask")
    ap.add_argument("--lang", default="en", help="Language code (en, hi, hinglish)")
    ap.add_argument("--timing", action="store_true", help="Print per-stage timing")
    args = ap.parse_args()

    from backend.app.graph.db import get_db
    from backend.app.llm.provider import get_llm, embed
    from backend.app.retrieval import cypher as Q
    from backend.app.retrieval.graphrag import GraphRAG
    from backend.app.reasoning import confidence as conf

    db = get_db()
    llm = get_llm()
    rag = GraphRAG(db, llm)

    if args.timing:
        # Manual stage timing
        t0 = time.time()
        q = rag.normalize(args.question, args.lang)
        t_norm = time.time()

        ents = rag.link_entities(q)
        t_link = time.time()

        entity_ids = [e["id"] for e in ents]
        rows = rag.fetch(entity_ids)
        t_fetch = time.time()

        if not rows:
            emb = embed([q])[0]
            rows, _ = rag.vector_fallback(emb)
        t_vec = time.time()

        print(f"  normalize:  {(t_norm - t0)*1000:.0f}ms", file=sys.stderr)
        print(f"  link:        {(t_link - t_norm)*1000:.0f}ms  ({len(ents)} entities)", file=sys.stderr)
        print(f"  fetch:       {(t_fetch - t_link)*1000:.0f}ms  ({len(rows)} rows)", file=sys.stderr)
        print(f"  vector fb:   {(t_vec - t_fetch)*1000:.0f}ms", file=sys.stderr)

    # Full answer (includes its own timing internally)
    resp = rag.answer(args.question, args.lang)
    data = resp.model_dump()

    print(json.dumps(data, indent=2, default=str))

    # Summary on stderr
    print(f"\n  status: {resp.status}", file=sys.stderr)
    print(f"  latency: {resp.latency_ms}ms", file=sys.stderr)
    if resp.status == "answered":
        print(f"  confidence: {resp.confidence.label} ({resp.confidence.score})", file=sys.stderr)
        print(f"  evidence: {len(resp.evidence)} items", file=sys.stderr)
        print(f"  decision: {resp.decision['title'][:60] if resp.decision else 'N/A'}", file=sys.stderr)
    else:
        print(f"  reason: {resp.refusal_reason}", file=sys.stderr)


if __name__ == "__main__":
    main()
