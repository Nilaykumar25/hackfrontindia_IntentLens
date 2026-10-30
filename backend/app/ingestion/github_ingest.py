"""Stage 1b: GitHub GraphQL -> data/cache/threads.jsonl.

Fetches merged PRs that touch the configured subsystem paths, with all
their review comments and linked issues.

Robustness notes:
  - Null authors: any node whose `author` field is null (deleted accounts,
    bots, ghost) is replaced by an empty string — never crashes.
  - Primary rate limit: `rateLimit.remaining` checked after every page;
    sleeps until `resetAt` if < 5 points remain.
  - Secondary rate limit: HTTP 429 with a `Retry-After` header is honoured;
    also backs off on 502/503/504.
  - Comment pagination: the query fetches `first:100` comments per PR.
    PRs with > 100 comments are rare for the redis subsystem, but we detect
    the truncation and log a warning so it can be followed up with a
    dedicated comment-fetch pass if needed.
  - Review inline comments: also fetched with `first:100`.
  - All cursor-based pagination loops until `hasNextPage` is False or the
    `max_prs` cap is reached.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone

import httpx

from ..config import settings
from ..models import Comment, Thread

URL = "https://api.github.com/graphql"

# ---------------------------------------------------------------------------
# GraphQL query — paginated list (existing behaviour)
# ---------------------------------------------------------------------------
QUERY = """
query($owner:String!, $name:String!, $after:String) {
  rateLimit { remaining resetAt cost }
  repository(owner:$owner, name:$name) {
    pullRequests(
      first: 25, after: $after,
      states: MERGED,
      orderBy: {field: UPDATED_AT, direction: DESC}
    ) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number title body url createdAt mergedAt
        author { login }
        files(first: 100) { nodes { path } }
        commits(first: 100) { nodes { commit { oid } } }
        comments(first: 100) {
          pageInfo { hasNextPage }
          nodes { id body url createdAt author { login } }
        }
        reviews(first: 50) {
          nodes {
            id body url submittedAt author { login }
            comments(first: 100) {
              nodes { id body url createdAt author { login } }
            }
          }
        }
        closingIssuesReferences(first: 10) {
          nodes {
            number title body url createdAt
            author { login }
            comments(first: 50) {
              nodes { id body url createdAt author { login } }
            }
          }
        }
      }
    }
  }
}
"""

# ---------------------------------------------------------------------------
# GraphQL query — single PR by number (used by --pr-numbers)
# ---------------------------------------------------------------------------
QUERY_SINGLE_PR = """
query($owner:String!, $name:String!, $number:Int!) {
  rateLimit { remaining resetAt cost }
  repository(owner:$owner, name:$name) {
    pullRequest(number: $number) {
      number title body url createdAt mergedAt
      author { login }
      files(first: 100) { nodes { path } }
      commits(first: 100) { nodes { commit { oid } } }
      comments(first: 100) {
        pageInfo { hasNextPage }
        nodes { id body url createdAt author { login } }
      }
      reviews(first: 50) {
        nodes {
          id body url submittedAt author { login }
          comments(first: 100) {
            nodes { id body url createdAt author { login } }
          }
        }
      }
      closingIssuesReferences(first: 10) {
        nodes {
          number title body url createdAt
          author { login }
          comments(first: 50) {
            nodes { id body url createdAt author { login } }
          }
        }
      }
    }
  }
}
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _login(node: dict | None) -> str:
    """Safely extract login from a nullable author node."""
    return (node or {}).get("login") or ""


def _to_comment(n: dict) -> Comment:
    return Comment(
        id=n["id"],
        author=_login(n.get("author")),
        created_at=n.get("createdAt") or n.get("submittedAt") or "",
        url=n.get("url") or "",
        body=n.get("body") or "",
    )


def _seen_ids(path: str) -> set[str]:
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as f:
        return {json.loads(l)["id"] for l in f if l.strip()}


def _is_in_paths(file_path: str, paths: list[str]) -> bool:
    fp = file_path.replace("\\", "/")
    for p in paths:
        pn = p.rstrip("/")
        if fp == pn or fp.startswith(pn + "/"):
            return True
    return False


def _reset_sleep(reset_at: str) -> None:
    """Sleep until the rate-limit resets, with a 5-second buffer."""
    try:
        reset = datetime.fromisoformat(reset_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        wait = max(0, (reset - now).total_seconds()) + 5
    except Exception:
        wait = 60
    print(f"  rate limit low — sleeping {wait:.0f}s until {reset_at}", file=sys.stderr)
    time.sleep(wait)


def _post(client: httpx.Client, variables: dict, attempt: int = 0) -> dict:
    """POST the paginated-list GraphQL query, retrying on transient errors."""
    return _post_query(client, QUERY, variables, attempt)


def _post_single(client: httpx.Client, variables: dict, attempt: int = 0) -> dict:
    """POST the single-PR GraphQL query, retrying on transient errors."""
    return _post_query(client, QUERY_SINGLE_PR, variables, attempt)


def _post_query(
    client: httpx.Client,
    query: str,
    variables: dict,
    attempt: int = 0,
) -> dict:
    """POST any GraphQL query, retrying on transient / rate-limit errors."""
    if attempt >= 6:
        raise RuntimeError("GitHub GraphQL failed after 6 attempts")

    r = client.post(URL, json={"query": query, "variables": variables})

    # Secondary rate limit — GitHub sends 429 with Retry-After
    if r.status_code == 429:
        wait = int(r.headers.get("Retry-After", "60"))
        print(f"  429 secondary rate limit — sleeping {wait}s", file=sys.stderr)
        time.sleep(wait)
        return _post_query(client, query, variables, attempt + 1)

    # Transient server errors
    if r.status_code in (502, 503, 504):
        wait = 2 ** attempt + 1
        print(f"  {r.status_code} transient — sleeping {wait}s", file=sys.stderr)
        time.sleep(wait)
        return _post_query(client, query, variables, attempt + 1)

    r.raise_for_status()
    data = r.json()

    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")

    rl = data["data"]["rateLimit"]
    if rl["remaining"] < 5:
        _reset_sleep(rl["resetAt"])

    return data["data"]


# ---------------------------------------------------------------------------
# Main ingest function
# ---------------------------------------------------------------------------

def ingest_prs(
    out_path: str | None = None,
    dry_run: bool = False,
    dry_run_limit: int = 3,
) -> int:
    """Fetch merged PRs touching SUBSYSTEM_PATHS and write Thread records.

    Args:
        out_path:       destination JSONL file (default: data/cache/threads.jsonl)
        dry_run:        if True, fetch at most `dry_run_limit` PRs and print a
                        summary without writing to disk.
        dry_run_limit:  how many PRs to fetch in dry-run mode.

    Returns number of new Thread records written (or fetched in dry-run).
    """
    out_path = out_path or os.path.join(settings.cache_dir, "threads.jsonl")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    seen = _seen_ids(out_path)
    cap = dry_run_limit if dry_run else settings.max_prs
    written = 0
    after: str | None = None

    headers = {"Authorization": f"bearer {settings.github_token}"}

    ctx = open(out_path, "a", encoding="utf-8") if not dry_run else None
    try:
        with httpx.Client(headers=headers, timeout=60) as client:
            while written < cap:
                data = _post(client, {
                    "owner": settings.repo_owner,
                    "name": settings.repo_name,
                    "after": after,
                })
                page = data["repository"]["pullRequests"]

                for pr in page["nodes"]:
                    if written >= cap:
                        break

                    tid = f"pr:{pr['number']}"
                    files = [f["path"] for f in pr["files"]["nodes"]]

                    # Skip if not touching the subsystem
                    if not any(_is_in_paths(f, settings.paths) for f in files):
                        continue
                    # Skip already-cached (resumability)
                    if tid in seen:
                        continue

                    # ── comments ──────────────────────────────────────────
                    pr_comments_page = pr["comments"]
                    comments: list[Comment] = [_to_comment(n) for n in pr_comments_page["nodes"]]
                    if pr_comments_page["pageInfo"]["hasNextPage"]:
                        print(
                            f"  Warning: pr:{pr['number']} has >100 comments; "
                            "only first 100 fetched. Add pagination pass if needed.",
                            file=sys.stderr,
                        )

                    # ── review comments ────────────────────────────────────
                    for rv in pr["reviews"]["nodes"]:
                        if rv.get("body", "").strip():
                            comments.append(
                                Comment(
                                    id=rv["id"],
                                    author=_login(rv.get("author")),
                                    created_at=rv.get("submittedAt") or "",
                                    url=rv.get("url") or "",
                                    body=rv["body"],
                                )
                            )
                        comments.extend(_to_comment(n) for n in rv["comments"]["nodes"])

                    # ── closing issues ─────────────────────────────────────
                    closes: list[int] = []
                    for iss in pr["closingIssuesReferences"]["nodes"]:
                        closes.append(iss["number"])
                        comments.extend(_to_comment(n) for n in iss["comments"]["nodes"])
                        # Inline the issue body as a synthetic comment for mining
                        comments.append(Comment(
                            id=f"issue-body:{iss['number']}",
                            author=_login(iss.get("author")),
                            created_at=iss["createdAt"],
                            url=iss["url"],
                            body=f"ISSUE #{iss['number']}: {iss['title']}\n{iss.get('body') or ''}",
                        ))

                    thread = Thread(
                        id=tid,
                        kind="pr",
                        number=pr["number"],
                        title=pr["title"],
                        body=pr.get("body") or "",
                        url=pr["url"],
                        author=_login(pr.get("author")),
                        created_at=pr["createdAt"],
                        merged_at=pr.get("mergedAt"),
                        comments=comments,
                        commit_shas=[c["commit"]["oid"] for c in pr["commits"]["nodes"]],
                        closes=closes,
                        files=files,
                    )

                    if dry_run:
                        _print_summary(thread)
                    else:
                        ctx.write(thread.model_dump_json() + "\n")  # type: ignore[union-attr]

                    written += 1

                if not page["pageInfo"]["hasNextPage"] or written >= cap:
                    break
                after = page["pageInfo"]["endCursor"]
    finally:
        if ctx:
            ctx.close()

    return written


def _print_summary(t: Thread) -> None:
    n_comments = len(t.comments)
    n_closes = len(t.closes)
    print(
        f"  PR #{t.number:5d}  |  {len(t.files):3d} files  |  "
        f"{n_comments:3d} comments  |  closes {n_closes} issue(s)  |  {t.title[:60]}"
    )


# ---------------------------------------------------------------------------
# Fetch specific PRs by number  (--pr-numbers)
# ---------------------------------------------------------------------------

def _build_thread_from_pr_node(pr: dict) -> Thread:
    """Shared logic: turn a GraphQL PR node into a Thread model."""
    files = [f["path"] for f in pr["files"]["nodes"]]

    pr_comments_page = pr["comments"]
    comments: list[Comment] = [_to_comment(n) for n in pr_comments_page["nodes"]]
    if pr_comments_page["pageInfo"]["hasNextPage"]:
        print(
            f"  Warning: pr:{pr['number']} has >100 comments; "
            "only first 100 fetched.",
            file=sys.stderr,
        )

    for rv in pr["reviews"]["nodes"]:
        if rv.get("body", "").strip():
            comments.append(Comment(
                id=rv["id"],
                author=_login(rv.get("author")),
                created_at=rv.get("submittedAt") or "",
                url=rv.get("url") or "",
                body=rv["body"],
            ))
        comments.extend(_to_comment(n) for n in rv["comments"]["nodes"])

    closes: list[int] = []
    for iss in pr["closingIssuesReferences"]["nodes"]:
        closes.append(iss["number"])
        comments.extend(_to_comment(n) for n in iss["comments"]["nodes"])
        comments.append(Comment(
            id=f"issue-body:{iss['number']}",
            author=_login(iss.get("author")),
            created_at=iss["createdAt"],
            url=iss["url"],
            body=f"ISSUE #{iss['number']}: {iss['title']}\n{iss.get('body') or ''}",
        ))

    return Thread(
        id=f"pr:{pr['number']}",
        kind="pr",
        number=pr["number"],
        title=pr["title"],
        body=pr.get("body") or "",
        url=pr["url"],
        author=_login(pr.get("author")),
        created_at=pr["createdAt"],
        merged_at=pr.get("mergedAt"),
        comments=comments,
        commit_shas=[c["commit"]["oid"] for c in pr["commits"]["nodes"]],
        closes=closes,
        files=files,
    )


def ingest_prs_by_number(
    pr_numbers: list[int],
    out_path: str | None = None,
    dry_run: bool = False,
) -> tuple[int, list[int]]:
    """Fetch specific PRs by number via the GraphQL pullRequest(number:) field.

    Ignores path filter and recency order — fetches exactly what is requested.
    Skips any PR whose id ("pr:<number>") is already in the output file.

    Args:
        pr_numbers:  list of GitHub PR numbers to fetch.
        out_path:    destination JSONL file (default: data/cache/threads.jsonl).
        dry_run:     if True, print summaries without writing to disk.

    Returns:
        (n_fetched, failed_numbers)
    """
    out_path = out_path or os.path.join(settings.cache_dir, "threads.jsonl")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    seen = _seen_ids(out_path)
    headers = {"Authorization": f"bearer {settings.github_token}"}

    fetched = 0
    failed: list[int] = []

    ctx = open(out_path, "a", encoding="utf-8") if not dry_run else None
    try:
        with httpx.Client(headers=headers, timeout=60) as client:
            for number in pr_numbers:
                tid = f"pr:{number}"
                if tid in seen:
                    print(f"  PR #{number:5d}  — already cached, skipping")
                    continue

                try:
                    data = _post_single(client, {
                        "owner": settings.repo_owner,
                        "name": settings.repo_name,
                        "number": number,
                    })
                except Exception as exc:
                    print(f"  PR #{number:5d}  — FAILED: {exc}", file=sys.stderr)
                    failed.append(number)
                    continue

                pr_node = data["repository"]["pullRequest"]
                if pr_node is None:
                    print(f"  PR #{number:5d}  — not found (null)", file=sys.stderr)
                    failed.append(number)
                    continue

                thread = _build_thread_from_pr_node(pr_node)

                if dry_run:
                    _print_summary(thread)
                else:
                    ctx.write(thread.model_dump_json() + "\n")  # type: ignore[union-attr]
                    print(f"  PR #{number:5d}  — fetched  ({len(thread.comments)} comments)")

                fetched += 1
    finally:
        if ctx:
            ctx.close()

    return fetched, failed


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Ingest GitHub PRs into threads.jsonl")
    ap.add_argument("--dry-run", action="store_true",
                    help="Fetch 3 PRs and print a summary without writing to disk")
    ap.add_argument("--dry-run-limit", type=int, default=3,
                    help="How many PRs to fetch in dry-run mode (default: 3)")
    ap.add_argument(
        "--pr-numbers",
        type=str,
        default=None,
        help=(
            "Comma-separated list of PR numbers to fetch by number "
            "(e.g. --pr-numbers 10092,9788,8474). "
            "Ignores path filter and recency order. "
            "Already-cached PRs are skipped automatically."
        ),
    )
    args = ap.parse_args()

    if not settings.github_token:
        print("GITHUB_TOKEN not set — aborting", file=sys.stderr)
        sys.exit(1)

    # ── --pr-numbers mode ────────────────────────────────────────────────────
    if args.pr_numbers:
        try:
            numbers = [int(x.strip()) for x in args.pr_numbers.split(",") if x.strip()]
        except ValueError as e:
            print(f"Invalid --pr-numbers value: {e}", file=sys.stderr)
            sys.exit(1)

        print(f"=== Fetching {len(numbers)} specific PR(s) by number ===")
        n, failed = ingest_prs_by_number(numbers, dry_run=args.dry_run)
        status = "fetched (dry run)" if args.dry_run else "written"
        print(f"\nPRs {status}: {n}")
        if failed:
            print(f"Failed ({len(failed)}): {failed}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    # ── normal paginated mode ────────────────────────────────────────────────
    if args.dry_run:
        print(f"=== Dry run: fetching up to {args.dry_run_limit} PRs from "
              f"{settings.repo_owner}/{settings.repo_name} ===")
    n = ingest_prs(dry_run=args.dry_run, dry_run_limit=args.dry_run_limit)
    print(f"threads {'fetched (dry run)' if args.dry_run else 'written'}: {n}")
