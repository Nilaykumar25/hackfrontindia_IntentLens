"""
scan_supersession.py
--------------------
Scans the three saved release-notes files for supersession candidates and
writes eval/supersession_candidates.md.

Supersession markers: default, deprecated, removed, replaced, no longer, changed.
Scope labels:
  in-scope  – concerns replication, persistence (RDB/AOF), or a redis.conf setting
  out-scope – clearly unrelated (Lua, ACL, cluster key-slot, HLL, streams, …)
  unsure    – cannot determine scope from line alone

Usage:
    python scripts/scan_supersession.py
"""

import re
from pathlib import Path

ROOT   = Path(__file__).parent.parent
CACHE  = ROOT / "data" / "cache"
EVAL   = ROOT / "eval"

BRANCHES = ["7.2", "7.0", "6.2"]

# ── supersession pattern ──────────────────────────────────────────────────────
SUP_RE = re.compile(
    r"\b(default|deprecated|removed|replaced|no longer|changed)\b",
    re.IGNORECASE,
)

# ── PR / issue reference ──────────────────────────────────────────────────────
PR_RE = re.compile(r"#(\d{4,})")

# ── in-scope keywords ─────────────────────────────────────────────────────────
# replication
REPL_KW = re.compile(
    r"\b(replica|replicas|replication|repl|slave|slaves|master|backlog|"
    r"psync|rdbchannelrepl|WAIT\b|WAITAOF\b|REPLCONF|diskless|full.?sync|"
    r"partial.?sync|rdb_save_incremental|propagated? to replica|"
    r"propagated? to slave)\b",
    re.IGNORECASE,
)
# persistence: RDB / AOF / snapshot
PERS_KW = re.compile(
    r"\b(RDB|AOF|aof|rdb|bgsave|bgrewriteaof|snapshot|persist|fsync|"
    r"appendonly|appendfsync|save\b|dump\.rdb|aof-use-rdb-preamble|"
    r"rdb-del-sync-files|lazyfree|propagated? to AOF)\b",
    re.IGNORECASE,
)
# redis.conf settings (common ones the user mentioned)
CONF_KW = re.compile(
    r"\b(maxmemory|hz\b|activerehashing|latency|slowlog|notify-keyspace|"
    r"bind\b|requirepass|timeout\b|tcp-keepalive|loglevel|databases\b|"
    r"activedefrag|lazyfree|proto-max-bulk|proto.max.bulk|client-output-buffer|"
    r"repl-backlog|repl-diskless|repl-timeout|min-slaves|min-replicas|"
    r"replica-lazy-flush|dynamic-hz|aof-rewrite-incremental-fsync|"
    r"rdb-save-incremental-fsync|sanitize-dump-payload|"
    r"set-max-intset-entries|shutdown-timeout|latency-tracking|"
    r"config option|config rewrite|config file)\b",
    re.IGNORECASE,
)

# ── clearly out-of-scope keywords ────────────────────────────────────────────
OOS_KW = re.compile(
    r"\b(Lua|EVAL\b|LDB|ACL\b|cluster bus|hash.?slot|HyperLogLog|HLL|"
    r"stream|XADD|XREAD|GEORADIUS|SORT_RO|cjson|cmsgpack|TLS|sentinel\b|"
    r"module\b|FUNCTION\b|SCRIPT\b|SUBSCRIBE\b|PUBLISH\b|keyspace.notif)\b",
    re.IGNORECASE,
)


def classify(line: str) -> str:
    if REPL_KW.search(line) or PERS_KW.search(line) or CONF_KW.search(line):
        if OOS_KW.search(line):
            return "unsure"
        return "in-scope"
    if OOS_KW.search(line):
        return "out-scope"
    return "unsure"


def scan_file(branch: str) -> list[dict]:
    path = CACHE / f"relnotes_{branch}.txt"
    if not path.exists():
        return []

    # PowerShell writes UTF-8-BOM; handle gracefully
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    lines = text.splitlines()
    results = []

    for lineno, line in enumerate(lines, 1):
        if not SUP_RE.search(line):
            continue
        stripped = line.strip()
        if not stripped or len(stripped) < 10:
            continue

        # For very short lines that are likely continuation fragments, grab
        # up to 2 surrounding lines for context (used only for classification).
        ctx_start = max(0, lineno - 3)
        ctx_end   = min(len(lines), lineno + 2)
        context   = " ".join(lines[ctx_start:ctx_end])

        # extract PR numbers from this line + immediate context
        all_prs = PR_RE.findall(context)
        prs = PR_RE.findall(line)  # prefer line-level first
        if not prs:
            prs = all_prs[:2]
        pr_str = ", ".join(f"#{p}" for p in dict.fromkeys(prs)) if prs else "—"

        # classify using the line text augmented with context
        scope = classify(stripped) if len(stripped) > 30 else classify(context)
        results.append({
            "branch": branch,
            "lineno": lineno,
            "line": stripped,
            "prs": pr_str,
            "scope": scope,
        })

    return results


def write_markdown(all_results: list[dict], path: Path):
    EVAL.mkdir(exist_ok=True)
    lines = [
        "# Supersession Candidates from Release Notes",
        "",
        "Sources: `data/cache/relnotes_7.2.txt`, `relnotes_7.0.txt`, `relnotes_6.2.txt`",
        "(extracted via `git show origin/<branch>:00-RELEASENOTES`)",
        "",
        "Supersession markers: **default, deprecated, removed, replaced, no longer, changed**",
        "",
        "Scope legend:",
        "- **in-scope** – concerns replication, RDB/AOF persistence, or a redis.conf setting",
        "- **out-scope** – clearly unrelated (Lua, ACL, TLS, cluster key-slots, HLL, …)",
        "- **unsure** – cannot determine scope from this line alone",
        "",
    ]

    for branch in BRANCHES:
        branch_rows = [r for r in all_results if r["branch"] == branch]
        in_scope  = [r for r in branch_rows if r["scope"] == "in-scope"]
        unsure    = [r for r in branch_rows if r["scope"] == "unsure"]
        out_scope = [r for r in branch_rows if r["scope"] == "out-scope"]

        lines += [
            f"## Branch {branch}",
            "",
            f"Total candidates: {len(branch_rows)}  "
            f"| in-scope: {len(in_scope)}  "
            f"| unsure: {len(unsure)}  "
            f"| out-scope: {len(out_scope)}",
            "",
            "| Line # | Scope | PR(s) | Text |",
            "|--------|-------|-------|------|",
        ]

        # show in-scope first, then unsure, then out-scope
        for row in (in_scope + unsure + out_scope):
            text_safe = row["line"].replace("|", "\\|")[:200]
            lines.append(
                f"| {row['lineno']} | **{row['scope']}** | {row['prs']} | {text_safe} |"
            )

        lines.append("")

    # summary
    in_scope_all = [r for r in all_results if r["scope"] == "in-scope"]
    lines += [
        "## Summary",
        "",
        f"- Total supersession-marker lines across all three branches: **{len(all_results)}**",
        f"- In-scope (replication / persistence / conf): **{len(in_scope_all)}**",
        f"- Unsure: **{len([r for r in all_results if r['scope'] == 'unsure'])}**",
        f"- Out-of-scope: **{len([r for r in all_results if r['scope'] == 'out-scope'])}**",
        "",
        "In-scope candidates (consolidated, deduplicated by text):",
        "",
        "| Branch | Line # | PR(s) | Text |",
        "|--------|--------|-------|------|",
    ]

    seen = set()
    for row in sorted(in_scope_all, key=lambda r: (r["branch"], r["lineno"])):
        key = row["line"][:120]
        if key in seen:
            continue
        seen.add(key)
        text_safe = row["line"].replace("|", "\\|")[:200]
        lines.append(
            f"| {row['branch']} | {row['lineno']} | {row['prs']} | {text_safe} |"
        )

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main():
    all_results = []
    for branch in BRANCHES:
        rows = scan_file(branch)
        all_results.extend(rows)
        in_s  = sum(1 for r in rows if r["scope"] == "in-scope")
        uns   = sum(1 for r in rows if r["scope"] == "unsure")
        oos   = sum(1 for r in rows if r["scope"] == "out-scope")
        print(f"  {branch}: {len(rows):4d} candidates  "
              f"(in-scope={in_s}, unsure={uns}, out-scope={oos})")

    out = EVAL / "supersession_candidates.md"
    write_markdown(all_results, out)

    total_in = sum(1 for r in all_results if r["scope"] == "in-scope")
    print(f"\nTotal candidates  : {len(all_results)}")
    print(f"In-scope total    : {total_in}")
    print(f"Written           : {out}")


if __name__ == "__main__":
    main()
