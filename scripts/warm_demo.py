"""Pre-ask the three demo questions so LLM caches are hot.

Run this before a demo to ensure sub-second response times:
    python -m scripts.warm_demo

The three questions match the EXAMPLES in App.jsx:
  1. "Why does always-show-logo exist in redis.conf?" — answered
  2. "Why does replicationCron avoid simultaneous BGSAVE and BGREWRITEAOF?" — superseded-aware
  3. "Why did the Redis team choose to use sds instead of C strings?" — refused

After warming, subsequent calls hit the LLM cache (instant) or the graph (fast).
"""
from __future__ import annotations

import sys
import time

from backend.app.graph.db import get_db
from backend.app.llm.provider import get_llm
from backend.app.retrieval.graphrag import GraphRAG


DEMO_QUESTIONS = [
    ("Why does always-show-logo exist in redis.conf?", "answered"),
    ("Why does replicationCron avoid simultaneous BGSAVE and BGREWRITEAOF?", "answered"),
    ("Why did the Redis team choose to use sds instead of C strings?", "refused"),
]


def main():
    print("=== Warming demo caches ===\n")
    rag = GraphRAG(get_db(), get_llm())

    all_ok = True
    for i, (q, expected) in enumerate(DEMO_QUESTIONS, 1):
        print(f"  [{i}/3] {q[:60]}...", end=" ", flush=True)
        t0 = time.time()
        resp = rag.answer(q)
        elapsed = time.time() - t0
        status_match = resp.status == expected
        marker = "✓" if status_match else "✗"
        print(f"{marker} {resp.status} ({elapsed:.1f}s)")
        if not status_match:
            print(f"       Expected {expected}, got {resp.status}")
            all_ok = False

    if all_ok:
        print("\n[PASS] All demo caches warm. Subsequent calls will be fast.")
    else:
        print("\n[WARN] Some demo questions did not match expected status.")
        print("       The demo may not behave as expected — check the graph.")


if __name__ == "__main__":
    main()
