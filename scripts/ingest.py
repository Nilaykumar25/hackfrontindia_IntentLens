"""Clone the repo (if needed) and run all three ingestion stages:
  1. Git commit history  -> data/cache/commits.jsonl
  2. GitHub PRs/issues   -> data/cache/threads.jsonl  (skipped without token)
  3. In-repo docs        -> data/cache/documents.jsonl
"""
import os
import sys
import subprocess

from backend.app.config import settings
from backend.app.ingestion.git_ingest import ingest_commits
from backend.app.ingestion.github_ingest import ingest_prs
from backend.app.ingestion.doc_ingest import ingest_docs


def main() -> None:
    # ── clone if needed ───────────────────────────────────────────────────────
    if not os.path.isdir(os.path.join(settings.repo_local_path, ".git")):
        url = f"https://github.com/{settings.repo_owner}/{settings.repo_name}.git"
        os.makedirs(os.path.dirname(settings.repo_local_path) or ".", exist_ok=True)
        print(f"Cloning {url} …")
        subprocess.run(["git", "clone", "--filter=blob:none", url,
                        settings.repo_local_path], check=True)

    # ── stage 1: git ──────────────────────────────────────────────────────────
    print("Stage 1: git history")
    n_commits = ingest_commits()
    print(f"  commits written: {n_commits}")

    # ── stage 2: GitHub ───────────────────────────────────────────────────────
    if settings.github_token:
        print("Stage 2: GitHub PRs/issues")
        n_threads = ingest_prs()
        print(f"  threads written: {n_threads}")
    else:
        print("Stage 2: GITHUB_TOKEN not set — skipping PR/issue ingestion")

    # ── stage 3: in-repo docs ─────────────────────────────────────────────────
    print("Stage 3: in-repo documents")
    n_docs = ingest_docs()
    print(f"  documents written: {n_docs}")


if __name__ == "__main__":
    main()
