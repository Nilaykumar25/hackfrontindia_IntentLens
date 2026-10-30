"""Smoke test against a deployed IntentLens instance.

Usage:
    python -m scripts.smoke_test https://your-url.onrender.com
"""
from __future__ import annotations

import sys
import time
import httpx


def check(base_url: str) -> bool:
    """Run smoke tests against the deployed API. Returns True if all pass."""
    base = base_url.rstrip("/")
    ok = True

    # 1. Health check
    print("  /health ...", end=" ", flush=True)
    try:
        r = httpx.get(f"{base}/health", timeout=10)
        if r.status_code == 200:
            print(f"OK ({r.json()['status']})")
        else:
            print(f"FAIL ({r.status_code})")
            ok = False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

    # 2. Ready check
    print("  /ready ...", end=" ", flush=True)
    try:
        r = httpx.get(f"{base}/ready", timeout=15)
        data = r.json()
        print(f"OK (neo4j={data['neo4j']}, llm={data['llm']['provider']})")
        if not data["neo4j"]:
            ok = False
    except Exception as e:
        print(f"ERROR: {e}")
        ok = False

    # 3. Ask a question
    print("  POST /ask ...", end=" ", flush=True)
    try:
        t0 = time.time()
        r = httpx.post(
            f"{base}/ask",
            json={"question": "Why does always-show-logo exist in redis.conf?"},
            timeout=30,
        )
        elapsed = time.time() - t0
        data = r.json()
        print(f"{data['status']} ({elapsed:.1f}s, conf={data.get('confidence', {}).get('label', 'N/A')})")
        if data["status"] == "refused":
            print("  WARN: demo question refused — check if graph is loaded")
    except Exception as e:
        print(f"ERROR: {e}")
        ok = False

    # 4. Entity graph
    print("  GET /entity/graph ...", end=" ", flush=True)
    try:
        r = httpx.get(f"{base}/entity/graph", params={"id": "config:bind"}, timeout=10)
        data = r.json()
        print(f"OK ({len(data['nodes'])} nodes)")
    except Exception as e:
        print(f"ERROR: {e}")
        ok = False

    return ok


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.smoke_test <base_url>")
        sys.exit(1)

    url = sys.argv[1]
    print(f"=== IntentLens smoke test: {url} ===")
    if check(url):
        print("\n[PASS] All checks passed.")
    else:
        print("\n[FAIL] One or more checks failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
