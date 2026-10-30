"""Unit tests for doc_ingest.py — all logic, no network, no Neo4j."""
from __future__ import annotations

import json
import os
from pathlib import Path

from backend.app.ingestion.doc_ingest import (
    DocRecord,
    _is_doc_candidate,
    _slug,
    extract_conf_sections,
    extract_doc_sections,
    ingest_docs,
)


# ── _slug ──────────────────────────────────────────────────────────────────────

def test_slug_lowercases():
    assert _slug("Hello World") == "hello-world"


def test_slug_collapses_special():
    assert _slug("Why ## the Code?") == "why-the-code"


def test_slug_strips_edges():
    assert not _slug("  --  ").startswith("-")


# ── _is_doc_candidate ─────────────────────────────────────────────────────────

def test_candidate_readme():
    assert _is_doc_candidate("README.md", [])


def test_candidate_changelog():
    assert _is_doc_candidate("CHANGELOG", [])


def test_candidate_md_extension():
    assert _is_doc_candidate("docs/design.md", [])


def test_candidate_rst():
    assert _is_doc_candidate("docs/api.rst", [])


def test_candidate_subsystem_conf():
    assert _is_doc_candidate("redis.conf", ["redis.conf"])


def test_candidate_not_c_file():
    assert not _is_doc_candidate("src/replication.c", [])


def test_candidate_not_random_txt_unless_matching():
    # .txt is included
    assert _is_doc_candidate("notes.txt", [])


# ── extract_conf_sections ─────────────────────────────────────────────────────

CONF_SAMPLE = """\
# The replication backlog is a buffer that accumulates slave data when slaves
# are disconnected for some time, so that when a slave wants to reconnect again,
# often a full resync is not needed.
repl-backlog-size 1mb

# After a master has no longer connected replicas for some time, the backlog
# will be freed.
repl-backlog-ttl 3600

# short comment
maxmemory 0
"""


def test_conf_extracts_documented_keys():
    recs = extract_conf_sections(CONF_SAMPLE, "redis.conf", "http://x")
    keys = [r.section for r in recs]
    assert "repl-backlog-size" in keys
    assert "repl-backlog-ttl" in keys


def test_conf_skips_short_comment():
    recs = extract_conf_sections(CONF_SAMPLE, "redis.conf", "http://x")
    # "short comment" is only 13 chars — below MIN_SECTION_CHARS — must be dropped
    keys = [r.section for r in recs]
    assert "maxmemory" not in keys


def test_conf_id_format():
    recs = extract_conf_sections(CONF_SAMPLE, "redis.conf", "http://x")
    for r in recs:
        assert r.id.startswith("redis.conf#config:")


def test_conf_text_capped():
    long_comment = "# " + "x " * 5000 + "\nsome-key value\n"
    recs = extract_conf_sections(long_comment, "redis.conf", "http://x")
    for r in recs:
        assert len(r.text) <= 8_000


# ── extract_doc_sections (markdown) ──────────────────────────────────────────

MD_SAMPLE = """\
# Redis Replication

Redis replication uses an asynchronous mechanism. The master sends commands
to replicas in a streaming fashion. This section documents the key decisions.

## Backlog size

The backlog is allocated on first connection. Default is 1 MB.
It was chosen to be small enough to avoid memory pressure on low-end servers.

## Replication ID

Each instance has a 40-character replication ID. It changes on failover.
"""


def test_md_extracts_sections():
    recs = extract_doc_sections(MD_SAMPLE, "README.md", "http://x")
    headings = [r.section for r in recs]
    assert any("Backlog" in h for h in headings)
    assert any("Replication ID" in h or "Replication" in h for h in headings)


def test_md_ids_are_unique():
    recs = extract_doc_sections(MD_SAMPLE, "README.md", "http://x")
    ids = [r.id for r in recs]
    assert len(ids) == len(set(ids))


def test_md_no_headings_single_chunk():
    text = "A" * 200
    recs = extract_doc_sections(text, "notes.md", "http://x")
    assert len(recs) == 1
    assert recs[0].id == "notes.md#chunk:0"


# ── extract_doc_sections (plain text) ────────────────────────────────────────

def test_plain_splits_on_double_newline():
    text = ("First paragraph " * 10) + "\n\n" + ("Second paragraph " * 10)
    recs = extract_doc_sections(text, "notes.txt", "http://x")
    assert len(recs) == 2


def test_plain_short_chunk_dropped():
    text = "tiny\n\n" + "Long enough paragraph. " * 10
    recs = extract_doc_sections(text, "notes.txt", "http://x")
    assert len(recs) == 1  # "tiny" is below MIN_SECTION_CHARS


# ── ingest_docs (integration, uses temp filesystem) ───────────────────────────

def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    # A redis.conf-style file with two documented keys
    (repo / "redis.conf").write_text(CONF_SAMPLE)
    # A markdown design doc
    (repo / "DESIGN.md").write_text(MD_SAMPLE)
    # An unrelated C file — must not be included
    (repo / "src" / "replication.c").write_text("// code")
    return repo


def test_ingest_docs_basic(tmp_path: Path):
    repo = _make_repo(tmp_path)
    out = tmp_path / "documents.jsonl"
    n = ingest_docs(
        repo_path=str(repo),
        subsystem_paths=["redis.conf"],
        out_path=str(out),
    )
    assert n > 0
    records = [json.loads(l) for l in out.read_text().splitlines()]
    assert len(records) == n


def test_ingest_docs_no_c_files(tmp_path: Path):
    repo = _make_repo(tmp_path)
    out = tmp_path / "documents.jsonl"
    ingest_docs(repo_path=str(repo), subsystem_paths=["redis.conf"], out_path=str(out))
    records = [json.loads(l) for l in out.read_text().splitlines()]
    # C source files must not appear; redis.conf is allowed (ends in .conf, not .c)
    assert all(not r["path"].endswith(".c") for r in records)


def test_ingest_docs_resumable(tmp_path: Path):
    repo = _make_repo(tmp_path)
    out = tmp_path / "documents.jsonl"
    n1 = ingest_docs(repo_path=str(repo), subsystem_paths=["redis.conf"], out_path=str(out))
    n2 = ingest_docs(repo_path=str(repo), subsystem_paths=["redis.conf"], out_path=str(out))
    assert n2 == 0
    lines = [l for l in out.read_text().splitlines() if l.strip()]
    assert len(lines) == n1  # no duplicates


def test_ingest_docs_ids_are_unique(tmp_path: Path):
    repo = _make_repo(tmp_path)
    out = tmp_path / "documents.jsonl"
    ingest_docs(repo_path=str(repo), subsystem_paths=["redis.conf"], out_path=str(out))
    ids = [json.loads(l)["id"] for l in out.read_text().splitlines()]
    assert len(ids) == len(set(ids))
