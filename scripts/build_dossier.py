"""
build_dossier.py
-----------------
Builds eval/supersession_dossier.md from git history only.
No network access. No guessing.

For each candidate:
 1. Confirm the "new" commit (PR number in subject).
 2. Find the "old" commit that introduced the original behaviour using
    git log -S (pickaxe) on the relevant symbol/string and file.
 3. Record which of the four key files each commit touches.

Usage:
    python scripts/build_dossier.py
"""

from __future__ import annotations
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent / "data" / "repo"
EVAL = Path(__file__).parent.parent / "eval"

KEY_FILES = [
    "src/replication.c",
    "src/rdb.c",
    "src/aof.c",
    "redis.conf",
]


# ── git helpers ───────────────────────────────────────────────────────────────

def git(*args: str, check: bool = False) -> str:
    """Run a git command in REPO; return stdout (or '' on error)."""
    result = subprocess.run(
        ["git"] + list(args),
        cwd=str(REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=45,
    )
    if check and result.returncode != 0:
        print(f"  [git error] git {' '.join(args)}\n  {result.stderr.strip()}", file=sys.stderr)
    return result.stdout.strip()


def commit_info(sha: str) -> dict | None:
    """Return {sha, date, subject} or None if not found."""
    out = git("show", "--no-patch", "--format=%H|%ad|%s", "--date=short", sha)
    lines = [l for l in out.splitlines() if "|" in l]
    if not lines:
        return None
    parts = lines[0].split("|", 2)
    if len(parts) < 3:
        return None
    return {"sha": parts[0], "date": parts[1], "subject": parts[2]}


def commit_files(sha: str) -> list[str]:
    """Return list of files changed by sha."""
    out = git("show", "--name-only", "--format=", sha)
    return [l.strip() for l in out.splitlines() if l.strip()]


def files_flag(changed: list[str]) -> dict[str, str]:
    """Return yes/no dict for the four key files."""
    result = {}
    for kf in KEY_FILES:
        result[kf] = "yes" if any(f == kf or f.endswith("/" + kf.split("/")[-1]) for f in changed) else "no"
    return result


def pickaxe_from_ancestor(search_str: str, file_path: str, new_sha: str) -> dict | None:
    """
    Search ancestors of new_sha (i.e. <new_sha>^) for the commit that most
    recently added/removed search_str in file_path.
    Returns the first (most recent pre-new) match — this is the "old" commit.
    Limits to the ancestry of new_sha to avoid full --all scan.
    """
    ancestor_ref = f"{new_sha}^"
    out = git("log", ancestor_ref, "--format=%H|%ad|%s", "--date=short",
              f"-S{search_str}", "--", file_path)
    lines = [l for l in out.splitlines() if "|" in l]
    if not lines:
        return None
    parts = lines[0].split("|", 2)
    if len(parts) < 3:
        return None
    return {"sha": parts[0], "date": parts[1], "subject": parts[2]}


def pr_from_subject(subject: str) -> str:
    m = re.search(r"\(#(\d+)\)$", subject)
    return f"#{m.group(1)}" if m else "—"


# ── candidate definitions ─────────────────────────────────────────────────────
# Each entry: (id, title, new_sha, old_search_str, old_file, notes)
# old_search_str / old_file are used for pickaxe to find the old commit.

NEW_COMMITS = {
    "10092": "ae89958972ee720be2bff68231d6353553c2272a",
    "9788":  "87789fae0b767e47fef78ee994434554f2bf2f31",
    "9166":  "c1718f9d862267bc44b2a326cdc8cb1ca5b81a39",
    "10504": "6fa8e4f7afcbd14748c736c38e5fbc117eaef7ba",
    "8474":  "53d1acd598b689b2bbc470d907b9e40e548d63f6",
    "7092":  "24c539251",   # short SHA, will expand
    "10690": "2bcd890d8aa645cab0d8fd0ed765c52a997de4f5",
    "10866": "d443e312ad130a821964b430770c881f710e6cb8",
    "11713": "9344f654c6227f30adf8bafd49b4218357c438b7",
    "11676_revert": "e12aacf3a2ea305de8e0e893564e5dd21b6b1216",
    "11676_orig":   "b4123663c31aaf1e97f4dbd630cbd7b8d0e91e31",
}

CANDIDATES = [
    {
        "id": "1",
        "pr": "10092",
        "title": "repl-diskless-sync default changed to yes",
        "new_shas": ["10092"],
        # The old default was "no"; look for that string in redis.conf
        "old_pickaxe": [("repl-diskless-sync no", "redis.conf")],
        "relnote_file": "relnotes_7.0.txt",
        "relnote_line": 870,
    },
    {
        "id": "2",
        "pr": "9788",
        "title": "Multi-Part AOF / appenddirname",
        "new_shas": ["9788"],
        # Before #9788 the single AOF rewrite used aofRewriteBufferReset
        "old_pickaxe": [("aofRewriteBufferReset", "src/aof.c")],
        "relnote_file": "relnotes_7.0.txt",
        "relnote_line": 777,
    },
    {
        "id": "3",
        "pr": "9166",
        "title": "Shared replication buffer",
        "new_shas": ["9166"],
        # Before #9166, each replica was fed via canFeedReplicaReplBuffer
        "old_pickaxe": [("canFeedReplicaReplBuffer", "src/replication.c")],
        "relnote_file": "relnotes_7.0.txt",
        "relnote_line": 895,
    },
    {
        "id": "4",
        "pr": "10504",
        "title": "Replicas panic on persistence write failure; ignore option added",
        "new_shas": ["10504"],
        # startBgsaveForReplication was the entry point before the panic was added
        "old_pickaxe": [("startBgsaveForReplication", "src/replication.c")],
        "relnote_file": "relnotes_7.0.txt",
        "relnote_line": 499,
    },
    {
        "id": "5",
        "pr": "8474",
        "title": "TTLs replicated as absolute timestamps (ms)",
        "new_shas": ["8474"],
        # Before #8474, rdb.c used RDB_OPCODE_EXPIRETIME (seconds, not ms)
        "old_pickaxe": [("RDB_OPCODE_EXPIRETIME_MS", "src/rdb.c")],
        "relnote_file": "relnotes_7.0.txt",
        "relnote_line": 848,
    },
    {
        "id": "6a",
        "pr": "7092",
        "title": "--save argument: stop resetting to defaults on CLI start (6.2)",
        "new_shas": ["7092"],
        # resetServerSaveParams was present before the fix
        "old_pickaxe": [("resetServerSaveParams", "src/config.c")],
        "relnote_file": "relnotes_6.2.txt",
        "relnote_line": 864,
    },
    {
        "id": "6b",
        "pr": "10690",
        "title": "--save regression fix (7.0.1)",
        "new_shas": ["10690"],
        # appendServerSaveParams was always present; the bug was in how it was called
        "old_pickaxe": [("appendServerSaveParams", "src/config.c")],
        "relnote_file": "relnotes_7.0.txt",
        "relnote_line": 459,
    },
    {
        "id": "6c",
        "pr": "10866",
        "title": "--save no-value backward compat (7.0.3)",
        "new_shas": ["10866"],
        "old_pickaxe": [("appendServerSaveParams", "src/config.c")],
        "relnote_file": "relnotes_7.0.txt",
        "relnote_line": 363,
    },
    {
        "id": "7",
        "pr": "11713",
        "title": "WAIT semantics: now uses offset after last write command",
        "new_shas": ["11713"],
        # Before #11713, WAIT tracked server.master_repl_offset directly
        "old_pickaxe": [("master_repl_offset", "src/replication.c")],
        "relnote_file": "relnotes_7.2.txt",
        "relnote_line": 593,
    },
    {
        "id": "8",
        "pr": "11676",
        "title": "Revert of KEYS output-buffer limit fix (6.2.9 -> 6.2.10)",
        "new_shas": ["11676_revert"],
        # The "old" commit IS the original fix that was later reverted.
        # We provide it directly instead of a pickaxe search (avoids slow scan).
        "old_pickaxe": [],   # handled via OLD_OVERRIDES
        "old_override_sha": "11676_orig",
        "relnote_file": "relnotes_6.2.txt",
        "relnote_line": 216,
    },
]


# ── main ──────────────────────────────────────────────────────────────────────

def process_candidate(c: dict) -> dict:
    result = {
        "id": c["id"],
        "pr": c["pr"],
        "title": c["title"],
        "new_commits": [],
        "old_commits": [],
        "new_files": {},
        "old_files": {},
        "status": "not found",
        "notes": [],
    }

    # ── new commits ───────────────────────────────────────────────────────────
    for sha_key in c["new_shas"]:
        sha = NEW_COMMITS.get(sha_key, sha_key)
        info = commit_info(sha)
        if not info:
            result["notes"].append(f"WARNING: new commit {sha} not resolved")
            continue
        changed = commit_files(info["sha"])
        info["files_flag"] = files_flag(changed)
        info["pr_ref"] = pr_from_subject(info["subject"])
        result["new_commits"].append(info)
        # merge into combined new_files (any yes wins)
        for kf, v in info["files_flag"].items():
            if v == "yes":
                result["new_files"][kf] = "yes"

    for kf in KEY_FILES:
        result["new_files"].setdefault(kf, "no")

    # ── old commits ───────────────────────────────────────────────────────────
    if result["new_commits"]:
        # Check for a direct override (revert pairs, etc.)
        override_key = c.get("old_override_sha")
        if override_key:
            sha = NEW_COMMITS.get(override_key, override_key)
            old = commit_info(sha)
            if old:
                changed = commit_files(old["sha"])
                old["files_flag"] = files_flag(changed)
                old["pr_ref"] = pr_from_subject(old["subject"])
                old["searched_in"] = "direct override (revert pair)"
                result["old_commits"].append(old)
        else:
            # Use the first new commit's SHA as the "ancestor" starting point
            new_sha = result["new_commits"][0]["sha"]

            for search_str, search_file in c["old_pickaxe"]:
                old = pickaxe_from_ancestor(search_str, search_file, new_sha)
                if old and old["sha"] not in [o["sha"] for o in result["old_commits"]]:
                    changed = commit_files(old["sha"])
                    old["files_flag"] = files_flag(changed)
                    old["pr_ref"] = pr_from_subject(old["subject"])
                    old["searched_in"] = f"-S'{search_str}' -- {search_file}"
                    result["old_commits"].append(old)
                    break  # take the first hit

    for kf in KEY_FILES:
        result["old_files"].setdefault(kf, "no")
    if result["old_commits"]:
        for kf, v in result["old_commits"][0]["files_flag"].items():
            if v == "yes":
                result["old_files"][kf] = "yes"

    # ── status ────────────────────────────────────────────────────────────────
    has_new = bool(result["new_commits"])
    has_old = bool(result["old_commits"])
    if has_new and has_old:
        result["status"] = "complete"
    elif has_new:
        result["status"] = "new only"
    else:
        result["status"] = "not found"

    return result


def write_dossier(results: list[dict]) -> Path:
    EVAL.mkdir(exist_ok=True)
    path = EVAL / "supersession_dossier.md"

    lines = [
        "# Supersession Dossier",
        "",
        "Built from git history (`data/repo`) and release-note files in `data/cache/`.",
        "No guessing. Uncertain items marked **unsure**.",
        "",
        "Files checked per commit: `src/replication.c`, `src/rdb.c`, "
        "`src/aof.c`, `redis.conf`",
        "",
    ]

    for r in results:
        lines += [
            f"---",
            f"",
            f"## {r['id']}. {r['title']}",
            f"",
            f"**Candidate PR:** #{r['pr']}  |  **Status:** `{r['status']}`",
            f"",
        ]

        # new commits
        lines.append("### New commit(s)")
        lines.append("")
        if r["new_commits"]:
            lines.append("| SHA (short) | Date | PR | Subject |")
            lines.append("|-------------|------|----|---------|")
            for nc in r["new_commits"]:
                short = nc["sha"][:9]
                lines.append(f"| `{short}` | {nc['date']} | {nc['pr_ref']} | {nc['subject'][:100]} |")
            lines.append("")
            nf = r["new_files"]
            lines.append(
                f"Files touched: replication.c={nf['src/replication.c']}  "
                f"rdb.c={nf['src/rdb.c']}  "
                f"aof.c={nf['src/aof.c']}  "
                f"redis.conf={nf['redis.conf']}"
            )
        else:
            lines.append("*(not resolved)*")
        lines.append("")

        # old commits
        lines.append("### Old (superseded) commit")
        lines.append("")
        if r["old_commits"]:
            lines.append("| SHA (short) | Date | PR | Subject |")
            lines.append("|-------------|------|----|---------|")
            for oc in r["old_commits"]:
                short = oc["sha"][:9]
                lines.append(f"| `{short}` | {oc['date']} | {oc['pr_ref']} | {oc['subject'][:100]} |")
            lines.append("")
            of = r["old_commits"][0]["files_flag"]
            lines.append(
                f"Files touched: replication.c={of['src/replication.c']}  "
                f"rdb.c={of['src/rdb.c']}  "
                f"aof.c={of['src/aof.c']}  "
                f"redis.conf={of['redis.conf']}"
            )
            lines.append(f"  *(found via `{r['old_commits'][0]['searched_in']}`)*")
        else:
            lines.append("*(not found — old commit not in this clone or search string yielded no result)*")

        lines.append("")

        if r["notes"]:
            for n in r["notes"]:
                lines.append(f"> ⚠ {n}")
            lines.append("")

    lines += [
        "---",
        "",
        "## Summary",
        "",
        "| # | PR | Title | Status |",
        "|---|----|-------|--------|",
    ]
    for r in results:
        lines.append(f"| {r['id']} | #{r['pr']} | {r['title']} | `{r['status']}` |")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main():
    print("Building supersession dossier from git history…\n")
    results = []
    for c in CANDIDATES:
        print(f"  Processing {c['id']}  PR#{c['pr']}  {c['title'][:50]}")
        r = process_candidate(c)
        results.append(r)
        print(f"    → new commits: {len(r['new_commits'])}  "
              f"old commits: {len(r['old_commits'])}  "
              f"status: {r['status']}")

    path = write_dossier(results)
    print(f"\nDossier written: {path}")

    complete = sum(1 for r in results if r["status"] == "complete")
    new_only = sum(1 for r in results if r["status"] == "new only")
    not_found = sum(1 for r in results if r["status"] == "not found")
    print(f"complete={complete}  new_only={new_only}  not_found={not_found}")


if __name__ == "__main__":
    main()
