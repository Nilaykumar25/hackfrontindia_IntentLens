"""Stage 1c: in-repo design docs + config comment blocks -> data/cache/documents.jsonl.

Two extraction strategies:

1. Config files (*.conf):
   Redis config files have a well-known format: each directive is preceded by
   one or more comment lines that explain what it does.  We extract those
   comment blocks and pair them with the key they describe, producing one
   Document per documented key.  Example:

       # The replication backlog size...
       # ...more explanation...
       repl-backlog-size 1mb   <-- key

   Document id: "{path}#config:{key}"

2. Markdown / RST / plain text / CHANGELOG / DESIGN / README files:
   We split on heading lines (## or # for Markdown; === / --- underlines for
   RST; or every N chars for plain files) and emit one Document per section
   that is long enough to be useful (MIN_SECTION_CHARS).

   Document id: "{path}#{slug_of_heading}" or "{path}#chunk:{n}"

Both are resumable: already-written ids are skipped.
"""
from __future__ import annotations

import json
import os
import re
import textwrap
from dataclasses import dataclass
from pathlib import Path

from ..config import settings

# ── constants ─────────────────────────────────────────────────────────────────

# File globs (relative to repo root) that are always candidates regardless of
# whether they are in SUBSYSTEM_PATHS.
DOC_PATTERNS: list[str] = [
    "README*", "CHANGELOG*", "CHANGES*", "DESIGN*", "ARCHITECTURE*",
    "*.md", "*.rst",
]

# Only emit sections at least this long (avoids 2-word headings with no body).
MIN_SECTION_CHARS = 80

# Cap text per Document to avoid overloading embeddings downstream.
MAX_TEXT_CHARS = 8_000


# ── data class ────────────────────────────────────────────────────────────────

@dataclass
class DocRecord:
    id: str          # "{path}#{anchor}"
    path: str        # relative path from repo root
    section: str     # heading or config key
    url: str         # GitHub blob URL
    text: str        # body text (capped)

    def to_dict(self) -> dict:
        return {"id": self.id, "path": self.path, "section": self.section,
                "url": self.url, "text": self.text}


# ── helpers ───────────────────────────────────────────────────────────────────

def _slug(s: str) -> str:
    """Lower-case, keep only alnum and hyphens — safe for use in ids."""
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:80]


def _github_url(repo_owner: str, repo_name: str, rel_path: str) -> str:
    return f"https://github.com/{repo_owner}/{repo_name}/blob/unstable/{rel_path}"


def _load_seen(path: str) -> set[str]:
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as f:
        return {json.loads(l)["id"] for l in f if l.strip()}


# ── config file parser ────────────────────────────────────────────────────────

_CONF_KEY_RE = re.compile(r"^([a-z][a-z0-9-]+)\s", re.M)
_COMMENT_RE = re.compile(r"^#")


def extract_conf_sections(text: str, path: str, url: str) -> list[DocRecord]:
    """Extract documented key sections from a redis.conf-style file.

    Groups of consecutive comment lines immediately before a key directive
    are returned as one Document per key.
    """
    records: list[DocRecord] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        # Collect a comment block
        if line.startswith("#"):
            block: list[str] = []
            j = i
            while j < len(lines) and lines[j].startswith("#"):
                block.append(lines[j].lstrip("# ").rstrip())
                j += 1
            # Does a key directive follow immediately?
            if j < len(lines):
                m = _CONF_KEY_RE.match(lines[j])
                if m:
                    key = m.group(1)
                    body = "\n".join(block).strip()
                    if len(body) >= MIN_SECTION_CHARS:
                        records.append(DocRecord(
                            id=f"{path}#config:{key}",
                            path=path,
                            section=key,
                            url=url,
                            text=body[:MAX_TEXT_CHARS],
                        ))
                    i = j + 1
                    continue
        i += 1
    return records


# ── markdown / text splitter ──────────────────────────────────────────────────

_MD_HEADING_RE = re.compile(r"^#{1,3}\s+(.+)$", re.M)


def _split_markdown(text: str, path: str, url: str) -> list[DocRecord]:
    """Split on ## / # headings; emit one Document per section."""
    records: list[DocRecord] = []
    positions = [(m.start(), m.group(1).strip()) for m in _MD_HEADING_RE.finditer(text)]
    if not positions:
        # No headings — treat whole file as one chunk if long enough
        if len(text.strip()) >= MIN_SECTION_CHARS:
            records.append(DocRecord(
                id=f"{path}#chunk:0",
                path=path,
                section=Path(path).stem,
                url=url,
                text=text.strip()[:MAX_TEXT_CHARS],
            ))
        return records
    for idx, (pos, heading) in enumerate(positions):
        end = positions[idx + 1][0] if idx + 1 < len(positions) else len(text)
        body = text[pos:end].strip()
        if len(body) >= MIN_SECTION_CHARS:
            records.append(DocRecord(
                id=f"{path}#{_slug(heading)}",
                path=path,
                section=heading,
                url=url,
                text=body[:MAX_TEXT_CHARS],
            ))
    return records


def _split_rst(text: str, path: str, url: str) -> list[DocRecord]:
    """Split RST on title-underline sections (===, ---, ~~~)."""
    records: list[DocRecord] = []
    lines = text.splitlines()
    section_starts: list[tuple[int, str]] = []  # (line_index, title)
    for i in range(1, len(lines)):
        ul = lines[i].strip()
        if ul and all(c == ul[0] for c in ul) and ul[0] in "=-~^'\"`:." and len(ul) >= 3:
            title = lines[i - 1].strip()
            if title:
                section_starts.append((i - 1, title))
    if not section_starts:
        if len(text.strip()) >= MIN_SECTION_CHARS:
            records.append(DocRecord(
                id=f"{path}#chunk:0",
                path=path,
                section=Path(path).stem,
                url=url,
                text=text.strip()[:MAX_TEXT_CHARS],
            ))
        return records
    for idx, (line_idx, heading) in enumerate(section_starts):
        end_line = section_starts[idx + 1][0] if idx + 1 < len(section_starts) else len(lines)
        body = "\n".join(lines[line_idx:end_line]).strip()
        if len(body) >= MIN_SECTION_CHARS:
            records.append(DocRecord(
                id=f"{path}#{_slug(heading)}",
                path=path,
                section=heading,
                url=url,
                text=body[:MAX_TEXT_CHARS],
            ))
    return records


def _split_plain(text: str, path: str, url: str) -> list[DocRecord]:
    """For files without recognised structure, chunk by paragraph blocks."""
    records: list[DocRecord] = []
    chunks = re.split(r"\n{2,}", text.strip())
    for i, chunk in enumerate(chunks):
        chunk = chunk.strip()
        if len(chunk) >= MIN_SECTION_CHARS:
            records.append(DocRecord(
                id=f"{path}#chunk:{i}",
                path=path,
                section=f"{Path(path).stem} chunk {i}",
                url=url,
                text=chunk[:MAX_TEXT_CHARS],
            ))
    return records


def extract_doc_sections(text: str, path: str, url: str) -> list[DocRecord]:
    """Dispatch to the right splitter based on file extension."""
    ext = Path(path).suffix.lower()
    if ext == ".conf":
        return extract_conf_sections(text, path, url)
    if ext in (".md", ".markdown"):
        return _split_markdown(text, path, url)
    if ext in (".rst",):
        return _split_rst(text, path, url)
    return _split_plain(text, path, url)


# ── candidate file discovery ──────────────────────────────────────────────────

def _is_doc_candidate(rel_path: str, subsystem_paths: list[str]) -> bool:
    """Return True if the file is a doc/config candidate.

    A file qualifies if it is:
    - One of the configured subsystem paths (e.g. redis.conf), OR
    - A .md / .rst file anywhere in the repo, OR
    - A file whose name matches README*, CHANGELOG*, DESIGN*, ARCHITECTURE*
    """
    name = Path(rel_path).name
    # Configured subsystem path
    for p in subsystem_paths:
        if rel_path == p or rel_path.startswith(p.rstrip("/") + "/"):
            return True
    # Doc file by name pattern
    name_up = name.upper()
    for pat in ("README", "CHANGELOG", "CHANGES", "DESIGN", "ARCHITECTURE"):
        if name_up.startswith(pat):
            return True
    # Doc file by extension
    if Path(rel_path).suffix.lower() in (".md", ".rst", ".txt"):
        return True
    return False


def _find_candidates(repo_path: str, subsystem_paths: list[str]) -> list[str]:
    """Walk the repo and return relative paths of candidate files."""
    candidates: list[str] = []
    skip_dirs = {".git", "node_modules", "__pycache__", ".tox", "vendor"}
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in files:
            abs_path = os.path.join(root, fname)
            rel_path = os.path.relpath(abs_path, repo_path).replace("\\", "/")
            if _is_doc_candidate(rel_path, subsystem_paths):
                candidates.append(rel_path)
    return sorted(candidates)


# ── main entry point ──────────────────────────────────────────────────────────

def ingest_docs(
    repo_path: str | None = None,
    subsystem_paths: list[str] | None = None,
    out_path: str | None = None,
) -> int:
    """Extract design docs and config comment blocks from the repo.

    Returns the number of new Document records written.
    """
    repo_path = repo_path or settings.repo_local_path
    subsystem_paths = subsystem_paths or settings.paths
    out_path = out_path or os.path.join(settings.cache_dir, "documents.jsonl")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    seen = _load_seen(out_path)
    written = 0

    candidates = _find_candidates(repo_path, subsystem_paths)

    with open(out_path, "a", encoding="utf-8") as out_f:
        for rel_path in candidates:
            abs_path = os.path.join(repo_path, rel_path)
            try:
                text = Path(abs_path).read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            url = _github_url(settings.repo_owner, settings.repo_name, rel_path)
            records = extract_doc_sections(text, rel_path, url)

            for rec in records:
                if rec.id in seen:
                    continue
                out_f.write(json.dumps(rec.to_dict()) + "\n")
                seen.add(rec.id)
                written += 1

    return written


if __name__ == "__main__":
    print("documents written:", ingest_docs())
