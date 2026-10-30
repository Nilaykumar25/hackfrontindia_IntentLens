"""Unit tests for github_ingest.py — all network calls are mocked."""
from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from backend.app.ingestion.github_ingest import _is_in_paths, _login, _to_comment, ingest_prs
from backend.app.models import Comment


# ── pure-logic helpers ────────────────────────────────────────────────────────

def test_login_none_returns_empty():
    assert _login(None) == ""


def test_login_missing_key_returns_empty():
    assert _login({}) == ""


def test_login_extracts_value():
    assert _login({"login": "torvalds"}) == "torvalds"


def test_is_in_paths_exact():
    assert _is_in_paths("src/replication.c", ["src/replication.c"])


def test_is_in_paths_prefix():
    assert _is_in_paths("src/replication.c", ["src"])


def test_is_in_paths_no_partial():
    assert not _is_in_paths("src2/foo.c", ["src"])


def test_to_comment_null_author():
    n = {"id": "C1", "body": "hello", "url": "http://x", "createdAt": "2020-01-01", "author": None}
    c = _to_comment(n)
    assert c.author == ""
    assert c.body == "hello"


# ── fixture: minimal valid GraphQL response ───────────────────────────────────

def _make_page(prs: list[dict], has_next: bool = False, cursor: str = "END") -> dict:
    return {
        "rateLimit": {"remaining": 1000, "resetAt": "2099-01-01T00:00:00Z", "cost": 1},
        "repository": {
            "pullRequests": {
                "pageInfo": {"hasNextPage": has_next, "endCursor": cursor},
                "nodes": prs,
            }
        },
    }


def _make_pr(number: int, files: list[str], n_comments: int = 2) -> dict:
    return {
        "number": number,
        "title": f"PR {number}",
        "body": f"Body of PR {number}",
        "url": f"https://github.com/redis/redis/pull/{number}",
        "createdAt": "2022-01-01T00:00:00Z",
        "mergedAt": "2022-01-02T00:00:00Z",
        "author": {"login": f"user{number}"},
        "files": {"nodes": [{"path": f} for f in files]},
        "commits": {"nodes": [{"commit": {"oid": f"sha{number}abc"}}]},
        "comments": {
            "pageInfo": {"hasNextPage": False},
            "nodes": [
                {"id": f"C{number}-{i}", "body": f"comment {i}", "url": "http://c",
                 "createdAt": "2022-01-01T00:00:00Z", "author": {"login": "reviewer"}}
                for i in range(n_comments)
            ],
        },
        "reviews": {"nodes": []},
        "closingIssuesReferences": {"nodes": []},
    }


# ── mocked ingest_prs tests ───────────────────────────────────────────────────

def _mock_response(data: dict) -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"data": data}
    resp.raise_for_status = MagicMock()
    return resp


@patch("backend.app.ingestion.github_ingest.settings")
@patch("httpx.Client")
def test_ingest_prs_writes_matching_prs(mock_client_cls, mock_settings, tmp_path):
    mock_settings.github_token = "tok"
    mock_settings.repo_owner = "redis"
    mock_settings.repo_name = "redis"
    mock_settings.paths = ["src/replication.c"]
    mock_settings.max_prs = 100
    mock_settings.cache_dir = str(tmp_path)

    page = _make_page([
        _make_pr(1, ["src/replication.c"]),   # matches
        _make_pr(2, ["README.md"]),            # does NOT match
        _make_pr(3, ["src/replication.c", "src/rdb.c"]),  # matches
    ])
    mock_http = MagicMock()
    mock_http.__enter__ = MagicMock(return_value=mock_http)
    mock_http.__exit__ = MagicMock(return_value=False)
    mock_http.post.return_value = _mock_response(page)
    mock_client_cls.return_value = mock_http

    out = str(tmp_path / "threads.jsonl")
    n = ingest_prs(out_path=out)

    assert n == 2, f"expected 2 matching PRs, got {n}"
    records = [json.loads(l) for l in open(out).readlines()]
    assert len(records) == 2
    ids = {r["id"] for r in records}
    assert ids == {"pr:1", "pr:3"}


@patch("backend.app.ingestion.github_ingest.settings")
@patch("httpx.Client")
def test_ingest_prs_resumable(mock_client_cls, mock_settings, tmp_path):
    """Already-seen PR ids must be skipped."""
    mock_settings.github_token = "tok"
    mock_settings.repo_owner = "redis"
    mock_settings.repo_name = "redis"
    mock_settings.paths = ["src/replication.c"]
    mock_settings.max_prs = 100
    mock_settings.cache_dir = str(tmp_path)

    # Pre-populate cache with pr:1 already seen
    out = str(tmp_path / "threads.jsonl")
    existing = {"id": "pr:1", "kind": "pr", "number": 1, "title": "old",
                "body": "", "url": "", "author": "", "created_at": "",
                "merged_at": None, "comments": [], "commit_shas": [],
                "closes": [], "files": ["src/replication.c"]}
    with open(out, "w") as f:
        f.write(json.dumps(existing) + "\n")

    page = _make_page([
        _make_pr(1, ["src/replication.c"]),  # already in cache
        _make_pr(4, ["src/replication.c"]),  # new
    ])
    mock_http = MagicMock()
    mock_http.__enter__ = MagicMock(return_value=mock_http)
    mock_http.__exit__ = MagicMock(return_value=False)
    mock_http.post.return_value = _mock_response(page)
    mock_client_cls.return_value = mock_http

    n = ingest_prs(out_path=out)
    assert n == 1  # only pr:4 is new

    lines = open(out).readlines()
    assert len(lines) == 2  # original + pr:4


@patch("backend.app.ingestion.github_ingest.settings")
@patch("httpx.Client")
def test_ingest_prs_null_author(mock_client_cls, mock_settings, tmp_path):
    """PRs with null author (deleted account) must not crash."""
    mock_settings.github_token = "tok"
    mock_settings.repo_owner = "redis"
    mock_settings.repo_name = "redis"
    mock_settings.paths = ["src/replication.c"]
    mock_settings.max_prs = 100
    mock_settings.cache_dir = str(tmp_path)

    pr = _make_pr(99, ["src/replication.c"])
    pr["author"] = None  # simulate deleted account
    pr["comments"]["nodes"][0]["author"] = None  # null comment author too

    page = _make_page([pr])
    mock_http = MagicMock()
    mock_http.__enter__ = MagicMock(return_value=mock_http)
    mock_http.__exit__ = MagicMock(return_value=False)
    mock_http.post.return_value = _mock_response(page)
    mock_client_cls.return_value = mock_http

    out = str(tmp_path / "threads.jsonl")
    n = ingest_prs(out_path=out)
    assert n == 1

    record = json.loads(open(out).read())
    assert record["author"] == ""


@patch("backend.app.ingestion.github_ingest.settings")
@patch("httpx.Client")
def test_ingest_prs_dry_run_no_file(mock_client_cls, mock_settings, tmp_path, capsys):
    """Dry-run must not create/modify the output file."""
    mock_settings.github_token = "tok"
    mock_settings.repo_owner = "redis"
    mock_settings.repo_name = "redis"
    mock_settings.paths = ["src/replication.c"]
    mock_settings.max_prs = 100
    mock_settings.cache_dir = str(tmp_path)

    page = _make_page([_make_pr(1, ["src/replication.c"])])
    mock_http = MagicMock()
    mock_http.__enter__ = MagicMock(return_value=mock_http)
    mock_http.__exit__ = MagicMock(return_value=False)
    mock_http.post.return_value = _mock_response(page)
    mock_client_cls.return_value = mock_http

    out = str(tmp_path / "threads_dryrun.jsonl")
    n = ingest_prs(out_path=out, dry_run=True, dry_run_limit=1)
    assert n == 1
    assert not os.path.exists(out), "dry-run must not write to disk"
