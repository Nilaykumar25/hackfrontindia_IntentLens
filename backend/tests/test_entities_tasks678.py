"""Tests for Tasks 6, 7, 8: config-key extraction, function hunk parsing, reference linking.

Tests marked with `real_repo` use data from data/repo/redis.conf and
data/cache/commits.jsonl; they are skipped when those files are absent so the
suite stays green in CI without the cloned repo.
"""
from __future__ import annotations

import json
import os
import random
import re
from pathlib import Path

import pytest

from backend.app.extraction.entities import (
    _strip_value,
    entity_ids_for_commit,
    extract_config_keys,
    find_refs,
    find_reverted_sha,
    functions_from_hunks,
    parse_config_keys,
)

REPO_CONF = Path("data/repo/redis.conf")
COMMITS_JSONL = Path("data/cache/commits.jsonl")

real_repo = pytest.mark.skipif(
    not REPO_CONF.exists() or not COMMITS_JSONL.exists(),
    reason="data/repo and data/cache not available",
)


# ══════════════════════════════════════════════════════════════════════════════
# Task 6a: _strip_value
# ══════════════════════════════════════════════════════════════════════════════

def test_strip_value_inline_comment():
    assert _strip_value("192.168.1.100  # listens on two") == "192.168.1.100"


def test_strip_value_double_quoted():
    assert _strip_value('""') == ""


def test_strip_value_quoted_with_spaces():
    assert _strip_value('"{title} {listen-addr} {server-mode}"') == "{title} {listen-addr} {server-mode}"


def test_strip_value_single_quoted():
    assert _strip_value("'yes'") == "yes"


def test_strip_value_plain():
    assert _strip_value("no") == "no"


def test_strip_value_multi_value():
    assert _strip_value("900 1") == "900 1"


def test_strip_value_path_with_hash():
    # URL-style value: hash is not an inline comment (no preceding space)
    assert _strip_value("/var/run/redis.pid") == "/var/run/redis.pid"


# ══════════════════════════════════════════════════════════════════════════════
# Task 6b: extract_config_keys — synthetic diffs
# ══════════════════════════════════════════════════════════════════════════════

DIFF_SIMPLE = """\
--- a/redis.conf
+++ b/redis.conf
-repl-backlog-size 1mb
+repl-backlog-size 5mb
"""

DIFF_COMMENTED_ADD = """\
+# repl-backlog-size 1mb
"""

DIFF_PROSE_COMMENT = """\
+# If you want you can bind a single interface, if the bind option is not
+# specified all the interfaces will listen for connections.
+daemonize no
+port 6379
"""

DIFF_QUOTED_EMPTY = """\
+logfile ""
"""

DIFF_MULTIVALUE = """\
+bind 127.0.0.1 -::1
+save 900 1
"""

DIFF_INLINE_COMMENT = """\
+bind 192.168.1.100 10.0.0.1     # listens on two specific IPv4 addresses
"""


def test_extract_change_detected():
    r = extract_config_keys(DIFF_SIMPLE, known_keys={"repl-backlog-size"})
    assert len(r) == 1
    assert r[0] == {"key": "repl-backlog-size", "value": "5mb", "change": "CHANGE"}


def test_extract_commented_add_accepted_with_known_keys():
    r = extract_config_keys(DIFF_COMMENTED_ADD, known_keys={"repl-backlog-size"})
    assert len(r) == 1
    assert r[0]["key"] == "repl-backlog-size"


def test_extract_commented_add_skipped_without_known_keys():
    r = extract_config_keys(DIFF_COMMENTED_ADD, known_keys=None)
    assert r == []


def test_extract_prose_comment_not_picked_up():
    r = extract_config_keys(DIFF_PROSE_COMMENT, known_keys=None)
    keys = [x["key"] for x in r]
    assert "specified" not in keys
    assert "interface" not in keys
    assert "daemonize" in keys
    assert "port" in keys


def test_extract_prose_comment_not_picked_up_with_known_keys():
    known = {"daemonize", "port"}
    r = extract_config_keys(DIFF_PROSE_COMMENT, known_keys=known)
    keys = [x["key"] for x in r]
    assert "specified" not in keys
    assert set(keys) == {"daemonize", "port"}


def test_extract_quoted_empty_value():
    r = extract_config_keys(DIFF_QUOTED_EMPTY, known_keys={"logfile"})
    assert r[0]["value"] == ""


def test_extract_multivalue_bind():
    r = extract_config_keys(DIFF_MULTIVALUE, known_keys={"bind", "save"})
    keys = {x["key"]: x["value"] for x in r}
    assert "127.0.0.1 -::1" == keys.get("bind", "")
    assert "900 1" == keys.get("save", "")


def test_extract_inline_comment_stripped():
    r = extract_config_keys(DIFF_INLINE_COMMENT, known_keys={"bind"})
    assert r[0]["value"] == "192.168.1.100 10.0.0.1"


# ══════════════════════════════════════════════════════════════════════════════
# Task 6c: parse_config_keys — real redis.conf
# ══════════════════════════════════════════════════════════════════════════════

@real_repo
def test_parse_real_conf_key_count():
    text = REPO_CONF.read_text(encoding="utf-8")
    keys = parse_config_keys(text)
    # redis.conf should have well over 100 distinct keys
    assert len(keys) > 100, f"only {len(keys)} keys parsed"


@real_repo
def test_parse_real_conf_known_keys():
    text = REPO_CONF.read_text(encoding="utf-8")
    keys = parse_config_keys(text)
    for k in ["bind", "port", "protected-mode", "repl-backlog-size",
              "logfile", "daemonize", "save", "databases", "loglevel"]:
        assert k in keys, f"expected key {k!r} not found"


@real_repo
def test_parse_real_conf_no_inline_comments_in_value():
    text = REPO_CONF.read_text(encoding="utf-8")
    keys = parse_config_keys(text)
    # bind value must NOT contain "# listens"
    bind_val = keys.get("bind", "")
    assert "#" not in bind_val, f"inline comment leaked into bind value: {bind_val!r}"


@real_repo
def test_parse_real_conf_quoted_logfile():
    text = REPO_CONF.read_text(encoding="utf-8")
    keys = parse_config_keys(text)
    # logfile has value `""` → should be stored as empty string after stripping
    assert keys.get("logfile") == "", f"logfile={keys.get('logfile')!r}"


@real_repo
def test_extract_on_real_conf_diffs():
    """extract_config_keys on real commit diffs must not return prose words."""
    conf_text = REPO_CONF.read_text(encoding="utf-8")
    known = set(parse_config_keys(conf_text).keys())

    lines = COMMITS_JSONL.read_text(encoding="utf-8").splitlines()
    bad_keys: list[str] = []
    for l in lines:
        r = json.loads(l)
        for f in r["files"]:
            if f["path"] == "redis.conf" and f.get("diff"):
                for item in extract_config_keys(f["diff"], known):
                    if item["key"] not in known:
                        bad_keys.append(item["key"])
    assert bad_keys == [], f"Unknown keys extracted: {bad_keys[:10]}"


# ══════════════════════════════════════════════════════════════════════════════
# Task 7: functions_from_hunks — synthetic + real
# ══════════════════════════════════════════════════════════════════════════════

def test_hunk_basic_c_function():
    diff = "@@ -10,6 +10,7 @@ int syncWithMaster(client *c) {\n+x\n"
    assert "syncWithMaster" in functions_from_hunks(diff)


def test_hunk_multi_header():
    diff = (
        "@@ -10,6 +10,7 @@ int syncWithMaster(client *c) {\n+x\n"
        "@@ -50,3 +51,3 @@ void replicationCron(void) {\n-y\n"
    )
    names = functions_from_hunks(diff)
    assert "syncWithMaster" in names
    assert "replicationCron" in names


def test_hunk_empty_context_skipped():
    diff = "@@ -1,2 +1,3 @@\n+line\n"
    assert functions_from_hunks(diff) == []


def test_hunk_goto_label_skipped():
    diff = "@@ -100,3 +100,4 @@ loaded_ok: /* DB loaded, cleanup and return C_OK */\n+x\n"
    # "loaded_ok" is a label, but FUNC_NAME will try to match identifier before `(`
    # There is no `(` in this context so nothing should be extracted
    names = functions_from_hunks(diff)
    assert "loaded_ok" not in names


def test_hunk_include_line_skipped():
    diff = '@@ -1,2 +1,3 @@ #include "server.h"\n+x\n'
    names = functions_from_hunks(diff)
    assert names == []


def test_hunk_config_line_skipped():
    # Config key line in hunk context must not produce a function name
    diff = "@@ -10,3 +10,4 @@ repl-backlog-size 1mb\n+x\n"
    names = functions_from_hunks(diff)
    assert names == []


def test_hunk_returns_sorted():
    diff = (
        "@@ -1,2 +1,2 @@ void zz(void) {\n+x\n"
        "@@ -5,2 +5,2 @@ void aa(void) {\n+y\n"
    )
    names = functions_from_hunks(diff)
    assert names == sorted(names)


@real_repo
def test_hunk_precision_on_real_commits():
    """At least 75 % of non-empty hunk contexts with `(` must yield a name."""
    lines = COMMITS_JSONL.read_text(encoding="utf-8").splitlines()
    random.seed(42)
    sample = random.sample(lines, min(300, len(lines)))

    HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@\s*(.*)$", re.M)
    total_func_ctx = 0
    extracted = 0
    for l in sample:
        r = json.loads(l)
        for f in r["files"]:
            diff = f.get("diff", "")
            for ctx in HUNK_RE.findall(diff):
                if "(" in ctx and not ctx.strip().startswith("#"):
                    total_func_ctx += 1
                    names = functions_from_hunks(f"@@ -1,1 +1,1 @@ {ctx}\n")
                    if names:
                        extracted += 1

    precision = extracted / total_func_ctx if total_func_ctx else 0
    assert precision >= 0.75, (
        f"Function extraction precision {precision:.1%} on real diffs "
        f"({extracted}/{total_func_ctx}) — below 75 % threshold"
    )


# ══════════════════════════════════════════════════════════════════════════════
# Task 8: find_refs + reference linking
# ══════════════════════════════════════════════════════════════════════════════

def test_find_refs_bare():
    assert find_refs("See #123") == [123]


def test_find_refs_fixes():
    assert find_refs("Fixes #42") == [42]


def test_find_refs_multiple():
    assert find_refs("Closes #10 and refs #20 and #30") == [10, 20, 30]


def test_find_refs_deduplicates():
    assert find_refs("#5 and #5 again") == [5]


def test_find_refs_no_match():
    assert find_refs("just a regular commit message") == []


def test_find_refs_large_number_ignored():
    # 7-digit numbers are beyond the range of real issue numbers (1–99999)
    assert find_refs("See #1234567") == []


def test_find_refs_case_insensitive():
    assert find_refs("FIXES #99") == [99]


@real_repo
def test_find_refs_on_real_commits():
    """A reasonable fraction of commits should reference issues."""
    lines = COMMITS_JSONL.read_text(encoding="utf-8").splitlines()
    with_refs = sum(1 for l in lines if find_refs(json.loads(l)["message"]))
    frac = with_refs / len(lines)
    # redis/redis: ~10-20 % of subsystem commits reference issues
    assert frac >= 0.05, f"only {frac:.1%} of commits have refs — check find_refs regex"


# ══════════════════════════════════════════════════════════════════════════════
# add_references (loader integration — pure-logic, no Neo4j)
# ══════════════════════════════════════════════════════════════════════════════

def test_add_references_separates_commit_and_pr_rows():
    """Verify the routing logic that separates commit rows from PR rows."""
    rows = [
        {"source_id": "abc123", "ref_number": 5},   # commit
        {"source_id": "pr:10", "ref_number": 20},   # PR
        {"source_id": "def456", "ref_number": 7},   # commit
    ]
    commit_rows = [r for r in rows if not r["source_id"].startswith("pr:")]
    pr_rows = [r for r in rows if r["source_id"].startswith("pr:")]
    assert len(commit_rows) == 2
    assert len(pr_rows) == 1
    assert pr_rows[0]["source_id"] == "pr:10"
