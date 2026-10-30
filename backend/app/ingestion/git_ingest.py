"""Stage 1a: git history -> data/cache/commits.jsonl (resumable).

Performance strategy:
  `git log --format=%H -- <paths>` pre-selects only the SHAs that touch the
  subsystem, so PyDriller never walks unrelated commits.  For redis/redis
  (~13 k commits total) this reduces traversal from O(all) to O(matching).

Resumability:
  Already-written SHAs are loaded from the output file at startup; only the
  delta is fetched.  Re-running the command is safe and additive.

Rename detection:
  PyDriller exposes `m.old_path` and `m.new_path` separately.  We store both
  so downstream code can maintain a single File identity across renames.
"""
from __future__ import annotations

import json
import os
import subprocess
from typing import Sequence

from pydriller import Repository
from tqdm import tqdm

from ..config import settings
from ..models import CommitRecord, FileChange


# ── helpers ──────────────────────────────────────────────────────────────────

def _load_seen(path: str) -> set[str]:
    """Return set of SHAs already written to the output file."""
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as f:
        return {json.loads(line)["sha"] for line in f if line.strip()}


def _relevant_shas(repo_path: str, paths: Sequence[str], max_commits: int) -> list[str]:
    """Fast pre-selection via `git log -- <paths>`.

    Returns SHAs in reverse-chronological order (newest first), capped at
    `max_commits`.  Raises subprocess.CalledProcessError if git is not
    available or the path is not a git repository.
    """
    cmd = [
        "git", "-C", repo_path,
        "log", "--format=%H",
        f"--max-count={max_commits}",
        "--",
        *paths,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _norm(p: str) -> str:
    """Normalise path separators to forward-slash (PyDriller returns OS-native)."""
    return p.replace("\\", "/")


def _is_in_paths(file_path: str, paths: Sequence[str]) -> bool:
    """True if `file_path` is exactly one of `paths` or is nested inside one.

    Normalises to forward-slash so the check works on Windows too.
    """
    fp = _norm(file_path)
    for p in paths:
        pn = _norm(p).rstrip("/")
        if fp == pn or fp.startswith(pn + "/"):
            return True
    return False


# ── main entry point ─────────────────────────────────────────────────────────

def ingest_commits(
    repo_path: str | None = None,
    paths: list[str] | None = None,
    out_path: str | None = None,
) -> int:
    """Ingest commits that touch `paths` into a JSONL file.

    Returns the number of new records written (0 if all already cached).
    """
    repo_path = repo_path or settings.repo_local_path
    paths = paths or settings.paths
    out_path = out_path or os.path.join(settings.cache_dir, "commits.jsonl")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    seen = _load_seen(out_path)

    # Fast pre-selection: only commits that actually touch the subsystem paths
    relevant = _relevant_shas(repo_path, paths, settings.max_commits)
    to_fetch = [sha for sha in relevant if sha not in seen]

    if not to_fetch:
        return 0

    written = 0
    with open(out_path, "a", encoding="utf-8") as out:
        for commit in tqdm(
            Repository(repo_path, only_commits=to_fetch).traverse_commits(),
            total=len(to_fetch),
            desc="commits",
        ):
            files: list[FileChange] = []
            for m in commit.modified_files:
                # Normalise OS-native separators (Windows returns backslashes)
                new_p = _norm(m.new_path or "")
                old_p = _norm(m.old_path or "")
                # Use the new path for filtering; fall back to old path for deletes
                canonical = new_p or old_p
                if not _is_in_paths(canonical, paths):
                    continue

                # Rename detection: store old_path only when the file was genuinely moved
                renamed_from: str | None = old_p if (old_p and new_p and old_p != new_p) else None

                files.append(
                    FileChange(
                        path=canonical,
                        old_path=renamed_from,
                        change_type=m.change_type.name,
                        diff=(m.diff or "")[:20_000],  # cap per file
                    )
                )

            if not files:
                continue

            rec = CommitRecord(
                sha=commit.hash,
                author=commit.author.name,
                email=commit.author.email.lower(),
                date=commit.author_date.isoformat(),
                message=commit.msg,
                files=files,
            )
            out.write(rec.model_dump_json() + "\n")
            written += 1

    return written


if __name__ == "__main__":
    print("commits written:", ingest_commits())
