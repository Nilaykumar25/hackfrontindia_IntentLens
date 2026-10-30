"""Unit tests for git_ingest.py using a real temporary git repository.

No mocking, no network.  We create a minimal git repo in a temp dir,
make a few commits, and verify that ingest_commits() produces the correct
JSONL output.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from backend.app.ingestion.git_ingest import (
    _is_in_paths,
    _load_seen,
    _relevant_shas,
    ingest_commits,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True,
                   capture_output=True, text=True)


def _make_repo(tmp_path: Path) -> Path:
    """Create a minimal git repo with commits touching subsystem paths."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@test.com")
    _git(repo, "config", "user.name", "Test User")

    # Commit 1: add a file inside the subsystem
    (repo / "src").mkdir()
    (repo / "src" / "replication.c").write_text("// v1\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "Add replication.c")

    # Commit 2: modify the subsystem file
    (repo / "src" / "replication.c").write_text("// v2 — bigger change\n" * 10)
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "Update replication.c")

    # Commit 3: rename the subsystem file
    _git(repo, "mv", "src/replication.c", "src/replication2.c")
    _git(repo, "commit", "-m", "Rename replication.c -> replication2.c")

    # Commit 4: unrelated file — must NOT appear in output
    (repo / "README.md").write_text("readme\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "Add readme (unrelated)")

    return repo


# ── _is_in_paths ──────────────────────────────────────────────────────────────

def test_is_in_paths_exact():
    assert _is_in_paths("redis.conf", ["redis.conf"])


def test_is_in_paths_nested():
    assert _is_in_paths("src/replication.c", ["src"])


def test_is_in_paths_no_partial_match():
    # "src2/foo" must not match path "src"
    assert not _is_in_paths("src2/foo.c", ["src"])


def test_is_in_paths_miss():
    assert not _is_in_paths("README.md", ["src/replication.c"])


# ── _load_seen ────────────────────────────────────────────────────────────────

def test_load_seen_empty(tmp_path: Path):
    assert _load_seen(str(tmp_path / "nonexistent.jsonl")) == set()


def test_load_seen_reads_shas(tmp_path: Path):
    f = tmp_path / "commits.jsonl"
    f.write_text('{"sha":"abc123","author":"x","email":"x","date":"2020","message":"m","files":[]}\n')
    assert _load_seen(str(f)) == {"abc123"}


# ── _relevant_shas ────────────────────────────────────────────────────────────

def test_relevant_shas_filters_to_subsystem(tmp_path: Path):
    repo = _make_repo(tmp_path)
    # Use forward-slash path; _relevant_shas passes it to git which handles both
    shas = _relevant_shas(str(repo), ["src/replication.c", "src/replication2.c"], 100)
    # Commits 1, 2, 3 touch the subsystem; commit 4 (README) must not appear
    assert len(shas) == 3


def test_relevant_shas_respects_max(tmp_path: Path):
    repo = _make_repo(tmp_path)
    shas = _relevant_shas(str(repo), ["src/replication.c", "src/replication2.c"], 1)
    assert len(shas) == 1


# ── ingest_commits ────────────────────────────────────────────────────────────

def test_ingest_commits_basic(tmp_path: Path):
    repo = _make_repo(tmp_path)
    out = tmp_path / "commits.jsonl"
    n = ingest_commits(
        repo_path=str(repo),
        paths=["src/replication.c", "src/replication2.c"],
        out_path=str(out),
    )
    assert n == 3, f"expected 3 commits, got {n}"
    records = [json.loads(l) for l in out.read_text().splitlines()]
    assert len(records) == 3


def test_ingest_commits_excludes_unrelated(tmp_path: Path):
    repo = _make_repo(tmp_path)
    out = tmp_path / "commits.jsonl"
    ingest_commits(repo_path=str(repo), paths=["src/replication.c", "src/replication2.c"], out_path=str(out))
    messages = [json.loads(l)["message"] for l in out.read_text().splitlines()]
    assert all("readme" not in m.lower() for m in messages), \
        "Unrelated README commit leaked into output"


def test_ingest_commits_resumable(tmp_path: Path):
    repo = _make_repo(tmp_path)
    out = tmp_path / "commits.jsonl"

    # First run
    n1 = ingest_commits(repo_path=str(repo), paths=["src/replication.c", "src/replication2.c"], out_path=str(out))
    assert n1 == 3

    # Second run — nothing new, should write 0
    n2 = ingest_commits(repo_path=str(repo), paths=["src/replication.c", "src/replication2.c"], out_path=str(out))
    assert n2 == 0

    # Total lines must still be 3 (not doubled)
    lines = [l for l in out.read_text().splitlines() if l.strip()]
    assert len(lines) == 3


def test_ingest_commits_rename_detection(tmp_path: Path):
    repo = _make_repo(tmp_path)
    out = tmp_path / "commits.jsonl"
    ingest_commits(repo_path=str(repo), paths=["src/replication.c", "src/replication2.c"], out_path=str(out))
    records = [json.loads(l) for l in out.read_text().splitlines()]
    # Find the rename commit
    rename_recs = [r for r in records if any(f["old_path"] for f in r["files"] if f["old_path"])]
    assert len(rename_recs) == 1, "Expected exactly one rename record"
    fc = rename_recs[0]["files"][0]
    assert fc["path"] == "src/replication2.c"
    assert fc["old_path"] == "src/replication.c"


def test_ingest_commits_diff_capped(tmp_path: Path):
    """Diffs must be capped at 20 000 chars."""
    repo = _make_repo(tmp_path)
    out = tmp_path / "commits.jsonl"
    ingest_commits(repo_path=str(repo), paths=["src/replication.c", "src/replication2.c"], out_path=str(out))
    for rec in (json.loads(l) for l in out.read_text().splitlines()):
        for f in rec["files"]:
            assert len(f["diff"]) <= 20_000
