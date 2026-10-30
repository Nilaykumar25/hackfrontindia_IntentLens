"""
audit_sources.py
----------------
Audits local and web sources for gold-set question candidates.
Uses ONLY raw text (comments, release notes, commit messages, threads).
Never touches Decision nodes or the answering pipeline.

Usage:
    python scripts/audit_sources.py
"""

import json
import os
import random
import re
import sys
import textwrap
import urllib.request
import urllib.error
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
REPO = ROOT / "data" / "repo"
CACHE = ROOT / "data" / "cache"
EVAL_DIR = ROOT / "eval"

# ── rationale markers (case-insensitive) ───────────────────────────────────────
RATIONALE_RE = re.compile(
    r"\b(because|in order to|to avoid|otherwise|this causes|trade[-\s]off|"
    r"instead of|to prevent|so that)\b",
    re.IGNORECASE,
)

# ── supersession markers for release notes ─────────────────────────────────────
SUPERSESSION_RE = re.compile(
    r"\b(changed default|deprecated|removed|replaced|no longer)\b",
    re.IGNORECASE,
)

MAX_PASSAGE = 600
THIN_THRESHOLD = 8
RANDOM_SEED = 42
NUM_EXAMPLES = 5

random.seed(RANDOM_SEED)

# ══════════════════════════════════════════════════════════════════════════════
# helpers
# ══════════════════════════════════════════════════════════════════════════════

def chunk_text(text: str, max_chars: int = MAX_PASSAGE) -> list[tuple[int, str]]:
    """
    Split *text* into non-overlapping paragraphs / blocks ≤ max_chars.
    Returns list of (start_line_1indexed, chunk_text).
    Splits on blank lines first, then hard-wraps oversized paragraphs.
    """
    lines = text.splitlines(keepends=True)
    chunks: list[tuple[int, str]] = []
    buf = []
    buf_start = 1  # 1-indexed

    for lineno, line in enumerate(lines, 1):
        if line.strip() == "" and buf:
            block = "".join(buf).strip()
            if block:
                # hard-wrap if still too long
                for part in _split_block(block, max_chars):
                    chunks.append((buf_start, part))
            buf = []
            buf_start = lineno + 1
        else:
            if not buf:
                buf_start = lineno
            buf.append(line)

    if buf:
        block = "".join(buf).strip()
        if block:
            for part in _split_block(block, max_chars):
                chunks.append((buf_start, part))

    return chunks


def _split_block(block: str, max_chars: int) -> list[str]:
    if len(block) <= max_chars:
        return [block]
    parts = []
    while len(block) > max_chars:
        cut = block.rfind(" ", 0, max_chars)
        if cut == -1:
            cut = max_chars
        parts.append(block[:cut].strip())
        block = block[cut:].strip()
    if block:
        parts.append(block)
    return parts


def passages_with_rationale(chunks: list[tuple[int, str]]) -> list[tuple[int, str]]:
    return [(ln, txt) for ln, txt in chunks if RATIONALE_RE.search(txt)]


def random_examples(passages: list[tuple[int, str]], n: int = NUM_EXAMPLES):
    pool = passages[:]
    random.shuffle(pool)
    return pool[:n]


def fmt_passage(label: str, ln: int, txt: str) -> str:
    preview = textwrap.shorten(txt, width=300, placeholder="…")
    return f"  [{label}  line {ln}]  {preview}"


# ══════════════════════════════════════════════════════════════════════════════
# source 1 – redis.conf  (comment blocks only)
# ══════════════════════════════════════════════════════════════════════════════

def audit_redis_conf() -> dict:
    path = REPO / "redis.conf"
    if not path.exists():
        return {"source": "redis.conf", "path": str(path), "passages": 0,
                "examples": [], "error": "FILE NOT FOUND"}

    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    # extract only comment lines (start with #)
    comment_blocks = []
    buf = []
    buf_start = 1

    for lineno, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            if not buf:
                buf_start = lineno
            buf.append(stripped.lstrip("# ").rstrip())
        else:
            if buf:
                comment_blocks.append((buf_start, "\n".join(buf)))
                buf = []
    if buf:
        comment_blocks.append((buf_start, "\n".join(buf)))

    # now chunk each comment block and test for rationale
    all_chunks = []
    for start_ln, block_text in comment_blocks:
        for part in _split_block(block_text, MAX_PASSAGE):
            all_chunks.append((start_ln, part))

    passages = passages_with_rationale(all_chunks)

    return {
        "source": "redis.conf (comments)",
        "path": str(path),
        "passages": len(passages),
        "examples": random_examples(passages),
    }


# ══════════════════════════════════════════════════════════════════════════════
# source 2 – C source files (comments only)
# ══════════════════════════════════════════════════════════════════════════════

def extract_c_comments(text: str) -> list[tuple[int, str]]:
    """
    Extract all /* ... */ block comments and // line-comment runs,
    returning (start_lineno_1indexed, comment_text) tuples.
    """
    lines = text.splitlines()
    results = []

    # ── block comments  /* ... */
    # We process the raw text to get line numbers
    pos = 0
    line_starts = [0]
    for ch in text:
        pos += 1
        if ch == "\n":
            line_starts.append(pos)

    def offset_to_line(off: int) -> int:
        lo, hi = 0, len(line_starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if line_starts[mid] <= off:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1  # 1-indexed

    block_re = re.compile(r"/\*.*?\*/", re.DOTALL)
    for m in block_re.finditer(text):
        content = m.group(0)
        # strip /* */ markers and leading * per line
        inner = re.sub(r"^/\*+\s*|\s*\*+/$", "", content.strip())
        inner = re.sub(r"^\s*\*+\s?", "", inner, flags=re.MULTILINE).strip()
        if inner:
            results.append((offset_to_line(m.start()), inner))

    # ── line comments  // ...  (consecutive runs merged)
    buf = []
    buf_start = 1
    for lineno, line in enumerate(lines, 1):
        m = re.match(r"^\s*//+\s?(.*)", line)
        if m:
            if not buf:
                buf_start = lineno
            buf.append(m.group(1))
        else:
            if buf:
                results.append((buf_start, "\n".join(buf)))
                buf = []
    if buf:
        results.append((buf_start, "\n".join(buf)))

    return results


def audit_c_file(relpath: str) -> dict:
    path = REPO / relpath
    if not path.exists():
        return {"source": relpath, "path": str(path), "passages": 0,
                "examples": [], "error": "FILE NOT FOUND"}

    text = path.read_text(encoding="utf-8", errors="replace")
    comment_blocks = extract_c_comments(text)

    all_chunks = []
    for start_ln, block_text in comment_blocks:
        for part in _split_block(block_text, MAX_PASSAGE):
            all_chunks.append((start_ln, part))

    passages = passages_with_rationale(all_chunks)

    return {
        "source": relpath,
        "path": str(path),
        "passages": len(passages),
        "examples": random_examples(passages),
    }


# ══════════════════════════════════════════════════════════════════════════════
# source 3 – 00-RELEASENOTES
# ══════════════════════════════════════════════════════════════════════════════

def audit_release_notes() -> dict:
    # discover file name
    candidates = list(REPO.glob("*RELEASE*")) + list(REPO.glob("*CHANGELOG*")) + \
                 list(REPO.glob("00-*"))
    release_file = None
    for c in candidates:
        if c.is_file():
            release_file = c
            break

    if release_file is None:
        return {"source": "release notes", "path": "NOT FOUND", "passages": 0,
                "examples": [], "supersession": [], "error": "FILE NOT FOUND"}

    text = release_file.read_text(encoding="utf-8", errors="replace")
    chunks = chunk_text(text)
    passages = passages_with_rationale(chunks)

    # supersession candidates
    supersession = []
    lines = text.splitlines()
    for lineno, line in enumerate(lines, 1):
        if SUPERSESSION_RE.search(line) and len(line.strip()) > 10:
            supersession.append((lineno, line.strip()))

    return {
        "source": f"release notes ({release_file.name})",
        "path": str(release_file),
        "passages": len(passages),
        "examples": random_examples(passages),
        "supersession": supersession,
    }


# ══════════════════════════════════════════════════════════════════════════════
# source 4a – data/cache/commits.jsonl
# ══════════════════════════════════════════════════════════════════════════════

def audit_commits() -> dict:
    path = CACHE / "commits.jsonl"
    if not path.exists():
        return {"source": "commits.jsonl", "path": str(path), "passages": 0,
                "examples": [], "error": "FILE NOT FOUND"}

    passages = []
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line_no, raw in enumerate(fh, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                continue
            # commit message is our raw text
            msg = obj.get("message", "")
            if not msg:
                continue
            for part in _split_block(msg, MAX_PASSAGE):
                if RATIONALE_RE.search(part):
                    sha = obj.get("sha", "?")[:8]
                    passages.append((line_no, f"[sha:{sha}] {part}"))

    return {
        "source": "commits.jsonl",
        "path": str(path),
        "passages": len(passages),
        "examples": random_examples(passages),
    }


# ══════════════════════════════════════════════════════════════════════════════
# source 4b – data/cache/threads.jsonl  (if present)
# ══════════════════════════════════════════════════════════════════════════════

def audit_threads() -> dict:
    path = CACHE / "threads.jsonl"
    if not path.exists():
        return {"source": "threads.jsonl", "path": str(path), "passages": 0,
                "examples": [], "error": "FILE NOT FOUND — skipped"}

    passages = []
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line_no, raw in enumerate(fh, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                continue
            # try common field names
            body = obj.get("body") or obj.get("text") or obj.get("content") or ""
            if not body:
                continue
            for part in _split_block(body, MAX_PASSAGE):
                if RATIONALE_RE.search(part):
                    src_id = obj.get("id") or obj.get("url") or f"line:{line_no}"
                    passages.append((line_no, f"[id:{src_id}] {part}"))

    return {
        "source": "threads.jsonl",
        "path": str(path),
        "passages": len(passages),
        "examples": random_examples(passages),
    }


# ══════════════════════════════════════════════════════════════════════════════
# web sources
# ══════════════════════════════════════════════════════════════════════════════

WEB_SOURCES = [
    ("redis.io replication docs",
     "https://redis.io/docs/management/replication/"),
    ("redis.io persistence docs",
     "https://redis.io/docs/management/persistence/"),
    ("antirez blog",
     "https://antirez.com"),
    ("GitHub redis releases",
     "https://github.com/redis/redis/releases"),
]


def try_fetch_url(url: str, timeout: int = 10) -> tuple[bool, str]:
    """Return (success, text_or_error)."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "audit_sources/1.0 (intentlens eval)"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(200_000)  # cap at 200 KB
            charset = resp.headers.get_content_charset("utf-8")
            return True, raw.decode(charset, errors="replace")
    except Exception as exc:
        return False, str(exc)


def audit_web_sources() -> list[dict]:
    results = []
    for name, url in WEB_SOURCES:
        ok, content = try_fetch_url(url)
        if not ok:
            results.append({
                "source": name,
                "url": url,
                "status": "manual check needed",
                "error": content,
                "passages": 0,
                "examples": [],
            })
            continue

        # strip HTML tags for plain-text passage extraction
        text = re.sub(r"<[^>]+>", " ", content)
        text = re.sub(r"&[a-z]+;", " ", text)
        text = re.sub(r"\s{2,}", " ", text)

        chunks = chunk_text(text)
        passages = passages_with_rationale(chunks)
        results.append({
            "source": name,
            "url": url,
            "status": "fetched",
            "passages": len(passages),
            "examples": random_examples(passages),
        })
    return results


# ══════════════════════════════════════════════════════════════════════════════
# print helpers
# ══════════════════════════════════════════════════════════════════════════════

def sep(char="─", n=80):
    print(char * n)


def print_source(result: dict, label: str):
    sep()
    print(f"SOURCE: {label}")
    print(f"  path   : {result.get('path') or result.get('url', '?')}")
    if result.get("error"):
        print(f"  status : {result['error']}")
    passages_count = result.get("passages", 0)
    usable = usability(passages_count)
    print(f"  passages with rationale markers: {passages_count}  [{usable}]")

    examples = result.get("examples", [])
    if examples:
        print(f"\n  ── {min(NUM_EXAMPLES, len(examples))} random examples ──")
        for ln, txt in examples:
            print(fmt_passage(result.get("path") or result.get("url", "?"), ln, txt))
            print()

    supersession = result.get("supersession", [])
    if supersession:
        print(f"\n  ── supersession candidates ({len(supersession)} lines) ──")
        for ln, line in supersession[:20]:  # show up to 20
            print(f"    line {ln:5d}: {textwrap.shorten(line, 120)}")
        if len(supersession) > 20:
            print(f"    … and {len(supersession)-20} more")


def usability(n: int) -> str:
    if n == 0:
        return "NO"
    if n < THIN_THRESHOLD:
        return "thin"
    return "yes"


# ══════════════════════════════════════════════════════════════════════════════
# markdown report
# ══════════════════════════════════════════════════════════════════════════════

def write_markdown(local_results: list[dict], web_results: list[dict]):
    EVAL_DIR.mkdir(exist_ok=True)
    md_path = EVAL_DIR / "source_audit.md"

    lines = [
        "# Source Audit for Gold-Set Questions",
        "",
        "Generated by `scripts/audit_sources.py`.",
        "Rationale markers: *because, in order to, to avoid, otherwise, this causes,",
        "trade-off, instead of, to prevent, so that*.",
        "A source is **thin** if it has fewer than 8 rationale passages; **no** if zero.",
        "",
        "## Local Sources",
        "",
        "| Source | Path | Passages | Usable | Notes |",
        "|--------|------|----------|--------|-------|",
    ]

    for r in local_results:
        n = r.get("passages", 0)
        u = usability(n)
        source = r["source"]
        path = r.get("path", "")
        error = r.get("error", "")
        notes = error if error else (
            f"{len(r.get('supersession', []))} supersession candidates"
            if r.get("supersession") is not None
            else ""
        )
        lines.append(f"| {source} | `{path}` | {n} | {u} | {notes} |")

    lines += [
        "",
        "## Web Sources",
        "",
        "| Source | URL | Passages | Usable | Notes |",
        "|--------|-----|----------|--------|-------|",
    ]

    for r in web_results:
        n = r.get("passages", 0)
        status = r.get("status", "?")
        u = "manual check needed" if status != "fetched" else usability(n)
        error = r.get("error", "")
        notes = f"BLOCKED: {textwrap.shorten(error, 80)}" if status != "fetched" else ""
        lines.append(
            f"| {r['source']} | [{r['url']}]({r['url']}) | {n} | {u} | {notes} |"
        )

    lines += [
        "",
        "## Supersession Candidates (Release Notes)",
        "",
        "Lines in `00-RELEASENOTES` that mention changed defaults, deprecated,",
        "removed, replaced, or 'no longer':",
        "",
    ]

    for r in local_results:
        if r.get("supersession") is not None:
            sups = r["supersession"]
            if sups:
                lines.append(f"**{r['source']}** — {len(sups)} lines found")
                lines.append("")
                lines.append("| Line | Text |")
                lines.append("|------|------|")
                for ln, txt in sups[:30]:
                    lines.append(f"| {ln} | {txt[:120]} |")
                if len(sups) > 30:
                    lines.append(f"| … | {len(sups)-30} more |")
                lines.append("")

    lines += [
        "## Priority Recommendation",
        "",
        "See console output for full analysis.",
        "",
    ]

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path


# ══════════════════════════════════════════════════════════════════════════════
# main
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 80)
    print("  INTENTLENS — SOURCE AUDIT FOR GOLD-SET QUESTIONS")
    print("  Raw text only. No Decision nodes. No pipeline output.")
    print("=" * 80)

    # ── local sources ──────────────────────────────────────────────────────────
    print("\n▶  Auditing local sources …\n")

    conf_result       = audit_redis_conf()
    replication_result = audit_c_file("src/replication.c")
    rdb_result        = audit_c_file("src/rdb.c")
    aof_result        = audit_c_file("src/aof.c")
    release_result    = audit_release_notes()
    commits_result    = audit_commits()
    threads_result    = audit_threads()

    local_results = [
        conf_result,
        replication_result,
        rdb_result,
        aof_result,
        release_result,
        commits_result,
        threads_result,
    ]

    for r in local_results:
        print_source(r, r["source"])

    # ── web sources ────────────────────────────────────────────────────────────
    print("\n")
    sep("═")
    print("▶  Attempting web sources …\n")

    web_results = audit_web_sources()
    for r in web_results:
        label = f"{r['source']}  ({r['url']})"
        print_source(r, label)

    # ── summary table ──────────────────────────────────────────────────────────
    sep("═")
    print("\nSUMMARY\n")
    all_results = local_results + web_results
    total_passages = sum(r.get("passages", 0) for r in all_results)

    print(f"{'Source':<40} {'Passages':>9}  {'Usable':>6}")
    print("-" * 60)
    for r in all_results:
        n = r.get("passages", 0)
        u = r.get("status", "") if r.get("status", "") == "manual check needed" \
            else usability(n)
        name = r["source"][:39]
        print(f"{name:<40} {n:>9}  {u:>6}")
    print("-" * 60)
    print(f"{'TOTAL':<40} {total_passages:>9}")

    # ── non-PR/commit count ───────────────────────────────────────────────────
    non_commit_sources = [
        conf_result, replication_result, rdb_result,
        aof_result, release_result,
    ] + [r for r in web_results if r.get("status") == "fetched"]

    non_commit_passages = sum(r.get("passages", 0) for r in non_commit_sources)

    print(f"\nPassages from non-commit/PR sources: {non_commit_passages}")
    print(f"Passages from commit messages:       {commits_result['passages']}")
    if threads_result.get("error"):
        print(f"Passages from threads (PR/issues):   UNAVAILABLE — {threads_result['error']}")
    else:
        print(f"Passages from threads (PR/issues):   {threads_result['passages']}")

    # ── priority recommendation ───────────────────────────────────────────────
    sep("═")
    print("\nPRIORITY RECOMMENDATION\n")

    ranked = sorted(
        [r for r in all_results if r.get("status", "") != "manual check needed"],
        key=lambda r: r.get("passages", 0),
        reverse=True,
    )

    print("To reach 30 answerable questions (≥15 from non-commit sources):\n")
    cumulative = 0
    for rank, r in enumerate(ranked, 1):
        n = r.get("passages", 0)
        if n == 0:
            continue
        cumulative += n
        note = " ← non-commit source" if r["source"] not in ("commits.jsonl", "threads.jsonl") else ""
        print(f"  {rank}. {r['source'][:50]:<52} {n:>5} passages{note}")
        if cumulative >= 30:
            print(f"\n     Cumulative passages reach 30 at rank {rank}.")

    print(f"\n  Non-commit passages available: {non_commit_passages}")
    if non_commit_passages >= 15:
        print("  ✓ ≥15 non-commit passages available — target is achievable.")
    else:
        print("  ✗ Fewer than 15 non-commit passages available.")
        print("    Prioritise fetching web sources manually (see 'manual check needed').")

    manual_check = [r for r in web_results if r.get("status") == "manual check needed"]
    if manual_check:
        print("\nMANUAL CHECK NEEDED (could not fetch):")
        for r in manual_check:
            print(f"  • {r['source']}")
            print(f"    URL : {r['url']}")
            print(f"    Why : {r.get('error', 'unknown')}")

    # ── write markdown ─────────────────────────────────────────────────────────
    md_path = write_markdown(local_results, web_results)
    print(f"\n✓  Audit report written to: {md_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
