"""
ingest_docs.py
--------------
Extracts Document records from raw source files and APPENDS them to
data/cache/documents.jsonl (skipping ids already present).

Sources:
  (a) redis.conf  — the comment block above each setting directive
  (b) src/replication.c, src/rdb.c, src/aof.c  — multi-line C comment
      blocks (/* ... */ or runs of //...) that contain at least one
      rationale marker.

Rationale markers:
  because, in order to, to avoid, otherwise, this causes, trade-off,
  instead of, to prevent, so that

Each record:
  id      "<relpath>#L<start>"          e.g. "redis.conf#L142"
  path    relative path inside the repo  e.g. "redis.conf"
  section human-readable section label   e.g. "tcp-backlog" or "fn:replicationCron"
  url     GitHub blob URL for that commit + line range
  text    the raw comment text (stripped of # / /* markers)
  source  "redis.conf" | "replication.c" | "rdb.c" | "aof.c"
  start_line / end_line  integers

Usage:
    python scripts/ingest_docs.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT       = Path(__file__).parent.parent
REPO       = ROOT / "data" / "repo"
CACHE      = ROOT / "data" / "cache"
OUT_FILE   = CACHE / "documents.jsonl"

RATIONALE_RE = re.compile(
    r"\b(because|in order to|to avoid|otherwise|this causes|trade[-\s]off|"
    r"instead of|to prevent|so that)\b",
    re.IGNORECASE,
)

# C source files to scan
C_FILES = [
    "src/replication.c",
    "src/rdb.c",
    "src/aof.c",
]

GITHUB_BASE = "https://github.com/redis/redis/blob"


# ── helpers ───────────────────────────────────────────────────────────────────

def repo_head_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() or "HEAD"


def github_url(sha: str, relpath: str, start: int, end: int) -> str:
    return f"{GITHUB_BASE}/{sha}/{relpath}#L{start}-L{end}"


def load_existing_ids() -> set[str]:
    if not OUT_FILE.exists():
        return set()
    ids = set()
    with OUT_FILE.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    ids.add(json.loads(line)["id"])
                except (json.JSONDecodeError, KeyError):
                    pass
    return ids


# ── redis.conf extraction ─────────────────────────────────────────────────────

def _is_directive(line: str) -> bool:
    """True if line is a non-comment, non-blank directive (setting name [value])."""
    s = line.strip()
    return bool(s) and not s.startswith("#")


def _strip_comment_marker(line: str) -> str:
    """Remove leading '# ' or '#' from a comment line."""
    s = line.strip()
    if s.startswith("# "):
        return s[2:]
    if s.startswith("#"):
        return s[1:]
    return s


def extract_conf_blocks(path: Path, relpath: str, sha: str) -> list[dict]:
    """
    Scan redis.conf.  For every directive line, collect the contiguous block
    of comment lines immediately above it (skipping any blank lines between
    comment blocks, but stopping at blanks or non-comment lines that separate
    two distinct blocks).

    Strategy:
      - Walk line-by-line.
      - When we hit a directive line, look backwards to collect the run of
        comment lines that ends immediately above it (no blank between last
        comment and the directive).
      - That block is the comment-above-setting.
    """
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    records: list[dict] = []

    for lineno, line in enumerate(lines):           # 0-indexed
        if not _is_directive(line):
            continue
        directive_name = line.strip().split()[0]    # first token = setting name

        # walk backwards to find the comment block immediately above
        block_lines: list[tuple[int, str]] = []     # (1-indexed lineno, raw line)
        j = lineno - 1
        while j >= 0:
            prev = lines[j]
            if prev.strip() == "":
                # blank line: stop if we already have comment content
                if block_lines:
                    break
                # else keep looking (allow one blank between blocks? No — stop)
                break
            if prev.strip().startswith("#"):
                block_lines.append((j + 1, prev))  # 1-indexed
                j -= 1
            else:
                break  # non-blank, non-comment → stop

        if not block_lines:
            continue

        block_lines.reverse()   # now in top-to-bottom order
        start_line = block_lines[0][0]
        end_line   = lineno + 1   # include the directive line itself

        text = "\n".join(_strip_comment_marker(l) for _, l in block_lines).strip()
        if not text:
            continue

        doc_id  = f"{relpath}#L{start_line}"
        url     = github_url(sha, relpath, start_line, end_line)
        records.append({
            "id":         doc_id,
            "path":       relpath,
            "section":    directive_name,
            "url":        url,
            "text":       text,
            "source":     "redis.conf",
            "start_line": start_line,
            "end_line":   end_line,
        })

    return records


# ── C source extraction ───────────────────────────────────────────────────────

def _offset_to_line(line_starts: list[int], offset: int) -> int:
    """Convert a character offset to 1-indexed line number via binary search."""
    lo, hi = 0, len(line_starts) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if line_starts[mid] <= offset:
            lo = mid
        else:
            hi = mid - 1
    return lo + 1  # 1-indexed


def _build_line_starts(text: str) -> list[int]:
    starts = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            starts.append(i + 1)
    return starts


def _block_text_from_c_block(raw: str) -> str:
    """Strip /* */ markers and leading * from each line of a C block comment."""
    inner = re.sub(r"^/\*+\s*|\s*\*+/$", "", raw.strip())
    inner = re.sub(r"^\s*\*+\s?", "", inner, flags=re.MULTILINE)
    return inner.strip()


def _nearest_function(text: str, comment_end_offset: int) -> str:
    """
    Return the name of the nearest function definition that follows the comment,
    within the next 400 characters of text.
    Falls back to "unknown".
    """
    window = text[comment_end_offset: comment_end_offset + 400]
    # match:  returntype funcname(  or  static type funcname(
    m = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", window)
    if m:
        # skip common non-function tokens
        skip = {"if", "while", "for", "switch", "return", "sizeof", "assert",
                 "NULL", "void", "int", "char", "long", "unsigned", "static",
                 "inline", "do", "else"}
        name = m.group(1)
        if name not in skip:
            return name
    return "unknown"


def extract_c_blocks(path: Path, relpath: str, sha: str) -> list[dict]:
    """
    Extract from a C file all comment blocks (/* ... */ or consecutive //
    line runs) that contain at least one rationale marker.
    """
    text   = path.read_text(encoding="utf-8", errors="replace")
    lstarts = _build_line_starts(text)
    records: list[dict] = []
    seen_starts: set[int] = set()

    # ── /* ... */ block comments ──────────────────────────────────────────────
    for m in re.finditer(r"/\*.*?\*/", text, re.DOTALL):
        raw_block = m.group(0)
        block_text = _block_text_from_c_block(raw_block)
        if not RATIONALE_RE.search(block_text):
            continue
        start_line = _offset_to_line(lstarts, m.start())
        end_line   = _offset_to_line(lstarts, m.end())
        if start_line in seen_starts:
            continue
        seen_starts.add(start_line)
        section = _nearest_function(text, m.end())
        doc_id  = f"{relpath}#L{start_line}"
        url     = github_url(sha, relpath, start_line, end_line)
        records.append({
            "id":         doc_id,
            "path":       relpath,
            "section":    section,
            "url":        url,
            "text":       block_text,
            "source":     path.name,
            "start_line": start_line,
            "end_line":   end_line,
        })

    # ── // line-comment runs ───────────────────────────────────────────────────
    lines      = text.splitlines()
    run: list[tuple[int, str]] = []   # (1-indexed lineno, stripped text)
    run_start_offset = 0

    def _flush_run(run: list, run_start_off: int) -> None:
        if not run:
            return
        combined = "\n".join(t for _, t in run)
        if not RATIONALE_RE.search(combined):
            return
        start_line = run[0][0]
        end_line   = run[-1][0]
        if start_line in seen_starts:
            return
        seen_starts.add(start_line)
        # find offset of the end of the last run line to search for section name
        end_offset = lstarts[min(end_line, len(lstarts) - 1)]
        section = _nearest_function(text, end_offset)
        doc_id  = f"{relpath}#L{start_line}"
        url     = github_url(sha, relpath, start_line, end_line)
        records.append({
            "id":         doc_id,
            "path":       relpath,
            "section":    section,
            "url":        url,
            "text":       combined,
            "source":     path.name,
            "start_line": start_line,
            "end_line":   end_line,
        })

    for lineno, line in enumerate(lines, 1):
        # skip lines already covered by a block comment
        if lineno in seen_starts:
            if run:
                _flush_run(run, run_start_offset)
                run = []
            continue

        m2 = re.match(r"^\s*//+\s?(.*)", line)
        if m2:
            stripped = m2.group(1)
            if not run:
                run_start_offset = lstarts[lineno - 1] if lineno - 1 < len(lstarts) else 0
            run.append((lineno, stripped))
        else:
            if run:
                _flush_run(run, run_start_offset)
                run = []

    if run:
        _flush_run(run, run_start_offset)

    return records


# ── main ──────────────────────────────────────────────────────────────────────

def main(dry_run: bool = False) -> None:
    sha        = repo_head_sha()
    existing   = load_existing_ids()
    all_records: list[dict] = []

    # ── (a) redis.conf ────────────────────────────────────────────────────────
    conf_path = REPO / "redis.conf"
    conf_rel  = "redis.conf"
    conf_records = extract_conf_blocks(conf_path, conf_rel, sha)
    print(f"redis.conf        : {len(conf_records):4d} blocks extracted")
    all_records.extend(conf_records)

    # ── (b) C source files ────────────────────────────────────────────────────
    for relpath in C_FILES:
        fpath = REPO / relpath
        if not fpath.exists():
            print(f"  MISSING: {relpath}")
            continue
        recs = extract_c_blocks(fpath, relpath, sha)
        print(f"{relpath:<30}: {len(recs):4d} blocks extracted")
        all_records.extend(recs)

    # ── dedup against existing ids ────────────────────────────────────────────
    new_records = [r for r in all_records if r["id"] not in existing]
    skipped     = len(all_records) - len(new_records)
    print(f"\nTotal extracted   : {len(all_records)}")
    print(f"Already in cache  : {skipped}")
    print(f"New to write      : {len(new_records)}")

    if dry_run:
        print("\n[dry-run] not writing anything")
        _print_samples(new_records)
        return

    # ── write ─────────────────────────────────────────────────────────────────
    CACHE.mkdir(exist_ok=True)
    with OUT_FILE.open("a", encoding="utf-8") as fh:
        for rec in new_records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"\nWritten {len(new_records)} records to {OUT_FILE}")
    _print_samples(new_records)


def _print_samples(records: list[dict], n: int = 5) -> None:
    import random
    random.seed(99)
    sample = random.sample(records, min(n, len(records)))
    print(f"\n-- {len(sample)} random sample documents --")
    for r in sample:
        print(f"  id      : {r['id']}")
        print(f"  source  : {r['source']}")
        print(f"  section : {r['section']}")
        print(f"  url     : {r['url']}")
        preview = r["text"][:180].replace("\n", " ↵ ")
        print(f"  text    : {preview}")
        print()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Extract Document records into documents.jsonl")
    ap.add_argument("--dry-run", action="store_true",
                    help="Extract and print but do not write to documents.jsonl")
    args = ap.parse_args()
    main(dry_run=args.dry_run)
