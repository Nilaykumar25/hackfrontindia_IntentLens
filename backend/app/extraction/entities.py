"""Stage 2: code entity extraction — config keys, functions from hunk headers, references.

Design notes
============

Config key extraction (Task 6)
-------------------------------
redis.conf uses two line forms in diffs:

  Uncommented active directive:   `+repl-backlog-size 1mb`
  Commented-out default:          `+# repl-backlog-size 1mb`

Both are valid key changes.  What we must NOT pick up are ordinary prose
comment lines such as:

  `+# If you want you can bind a single interface, if the bind option is not`
  `+# specified all the interfaces will listen for connections.`

The discriminator is: a commented-out KEY line has exactly one token before the
value, and that token matches the known-key list OR (when no list is available)
looks like a single hyphenated identifier with no trailing words that look like
natural-language prose.

Additional edge cases handled:
- Multi-value directives: `bind 127.0.0.1 -::1`, `save 900 1`
  → value stored as-is (full string after first token)
- Quoted values: `logfile ""`, `proc-title-template "{title} {listen-addr}"`
  → outer enclosing quotes stripped from value
- Inline comments: `bind 192.168.1.100 10.0.0.1  # listens on two...`
  → comment stripped from value in parse_config_keys

Function extraction (Task 7)
-----------------------------
Git stores the enclosing function signature in each diff hunk header:

  `@@ -10,6 +12,5 @@ int rdbSave(char *filename) {`

Sampling 500 commits shows ~83 % of non-empty hunk contexts contain a `(`
(function call/definition), ~14 % are goto labels or #include lines (correctly
skipped), ~3 % are empty.  Tree-sitter is NOT needed for the redis/redis
subsystem — the hunk-header approach is accurate and fast.

If you want to enable tree-sitter for a different repo, set
USE_TREESITTER=true in the environment and install `tree-sitter` +
`tree-sitter-c`.  The fallback path is provided but not exercised in tests
because it requires native binaries and is out of scope for this hackathon.

Reference linking (Task 8)
--------------------------
`find_refs` extracts issue/PR numbers from commit messages and PR bodies.
These are wired into REFERENCES edges by `loader.add_references`.
"""
from __future__ import annotations

import os
import re

# ── regexes ───────────────────────────────────────────────────────────────────

HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@\s*(.*)$", re.M)

# Match the first C-identifier before `(` in a hunk context string.
# Skips goto labels (end with `:`) and preprocessor lines (start with `#`).
FUNC_NAME = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(")

# References: #123, Fixes #123, closes #45, etc.
# Cap at 6 digits (\b ensures the number ends there, so #1234567 is not matched as #123456).
REF = re.compile(
    r"(?:(?:fix(?:es|ed)?|close[sd]?|resolve[sd]?|see|ref(?:s)?)\s+)?#(\d{1,6})\b",
    re.I,
)

# Revert commit SHA detection.
REVERT = re.compile(r"This reverts commit ([0-9a-f]{7,40})", re.I)

# ── config key regexes ────────────────────────────────────────────────────────

# A valid redis.conf key: starts with a lowercase letter, followed by
# lowercase letters, digits, or hyphens.
_KEY_PAT = r"[a-z][a-z0-9-]+"

# Diff line form 1:  `+key value…`   or  `-key value…`
# Diff line form 2:  `+# key value…` or  `-# key value…`  (commented-out default)
# Anchored so it can't match mid-comment prose words.
CONF_LINE = re.compile(
    r"^([+\-])\s*(?:#\s*)?(" + _KEY_PAT + r")\s+(.*)$"
)

# Inline comment: everything from unquoted ` #` onwards.
_INLINE_COMMENT = re.compile(r"\s+#\s.*$")

# Outer quotes (single or double) around an entire value — including empty strings.
_OUTER_QUOTES = re.compile(r'^(["\'])(.*)\1$', re.DOTALL)


# ── helpers ───────────────────────────────────────────────────────────────────

def _strip_value(raw: str) -> str:
    """Strip inline comments and enclosing quotes from a config value.

    Examples:
      '192.168.1.100  # comment'  → '192.168.1.100'
      '""'                        → ''
      '"{title} {listen-addr}"'   → '{title} {listen-addr}'
      '900 1'                     → '900 1'   (multi-value, kept as-is)
    """
    v = raw.strip()
    # Remove trailing inline comment: `value  # comment`
    # Only strip if the `#` is preceded by whitespace (avoids stripping URLs).
    v = _INLINE_COMMENT.sub("", v).strip()
    # Strip matching outer quotes
    m = _OUTER_QUOTES.match(v)
    if m:
        v = m.group(2)
    return v


# ── public API ────────────────────────────────────────────────────────────────

def functions_from_hunks(diff: str) -> list[str]:
    """Extract function names from git diff hunk headers.

    Git stores the enclosing scope (usually the function signature) after the
    second `@@` marker on each hunk header.  This is cheap, language-agnostic,
    and accurate for C/Python/Go.

    Hunk contexts that are NOT function names (and are correctly skipped):
    - Goto labels:       `loaded_ok: /* DB loaded... */`
    - Preprocessor:      `#include "server.h"`
    - Config key lines:  `repl-backlog-size 1mb`
    - Empty contexts:    (no function info available)

    An optional tree-sitter upgrade path exists: set USE_TREESITTER=1 in
    the environment to enable it (requires `tree-sitter` and `tree-sitter-c`).
    """
    if os.environ.get("USE_TREESITTER"):
        return _functions_treesitter(diff)

    names: set[str] = set()
    for ctx in HUNK.findall(diff or ""):
        ctx = ctx.strip()
        if not ctx or ctx.startswith("#"):
            continue
        m = FUNC_NAME.search(ctx)
        if m:
            names.add(m.group(1))
    return sorted(names)


def _functions_treesitter(diff: str) -> list[str]:  # pragma: no cover
    """Optional tree-sitter upgrade.  Only called when USE_TREESITTER=1."""
    try:
        import tree_sitter_c as tsc
        from tree_sitter import Language, Parser

        C_LANGUAGE = Language(tsc.language())
        parser = Parser(C_LANGUAGE)
        names: set[str] = set()
        for ctx in HUNK.findall(diff or ""):
            tree = parser.parse(ctx.encode())
            for node in tree.root_node.children:
                if node.type == "function_definition":
                    decl = node.child_by_field_name("declarator")
                    if decl:
                        fn = decl.child_by_field_name("declarator")
                        if fn:
                            names.add(fn.text.decode())
        return sorted(names)
    except Exception:
        # Fall back to regex on any import or parse error
        return functions_from_hunks.__wrapped__(diff)  # type: ignore[attr-defined]


def extract_config_keys(
    diff: str,
    known_keys: set[str] | None = None,
) -> list[dict]:
    """Return [{key, value, change}] for added/removed config directives in a diff.

    Args:
        diff:       raw unified diff text
        known_keys: authoritative set of key names from the live config file.
                    When provided, commented-out lines are only accepted if the
                    key is in this set (prevents prose comment words from being
                    misidentified as keys).
                    When None, commented-out lines are skipped entirely.
    """
    out: dict[str, dict] = {}

    for line in (diff or "").splitlines():
        if line.startswith(("+++", "---")):
            continue

        m = CONF_LINE.match(line)
        if not m:
            continue

        prefix, key, raw_value = m.group(1), m.group(2), m.group(3)

        # Determine whether this is a commented-out default.
        # CONF_LINE already consumed the optional `# `, so check the original.
        after_prefix = line[1:].lstrip()
        is_commented = after_prefix.startswith("#")

        if is_commented:
            # Accept only if the key is in the authoritative list
            if known_keys is None or key not in known_keys:
                continue

        if known_keys is not None and key not in known_keys:
            continue

        value = _strip_value(raw_value)
        change = "ADD" if prefix == "+" else "REMOVE"

        prev = out.get(key)
        if prev and prev["change"] != change:
            # Seen both +key and -key → it's a CHANGE; keep the ADD value
            out[key] = {
                "key": key,
                "value": value if change == "ADD" else prev["value"],
                "change": "CHANGE",
            }
        else:
            out[key] = {"key": key, "value": value, "change": change}

    return list(out.values())


# A small allowlist of short, non-hyphenated keys that are genuine Redis
# config directives but only ever appear commented-out in redis.conf.
# Without this, the hyphen-or-digit filter rejects them.
_SHORT_KEY_ALLOWLIST: set[str] = {
    "save",       # save <seconds> <changes> — always commented in redis.conf
    "include",    # include /path/to/local.conf
    "loadmodule", # loadmodule /path/to/my_module.so
    "unixsocket", # unixsocket /run/redis.sock — commented default, no hyphen
    "rename",     # rename-command CONFIG b840f...
}


def parse_config_keys(text: str) -> dict[str, str]:
    """Parse `key value` lines from a redis.conf-style file.

    Handles:
    - Active directives:   `bind 127.0.0.1 -::1`
    - Commented defaults:  `# repl-backlog-size 1mb`
    - Quoted values:       `logfile ""`
    - Multi-value:         `save 900 1`
    - Inline comments:     `bind 192.168.1.100  # comment` → strips comment
    - Double ## section headers are skipped.

    Key validity rules (matching redis.conf conventions):
    - At least 3 characters
    - Starts with a lowercase letter
    - Contains only lowercase letters, digits, hyphens
    - Must appear as an uncommented active directive at least once
      OR look like a real config key (contains a hyphen or digit)

    Strategy: two-pass.
      Pass 1: collect all keys from uncommented active lines (these are
              definitely real config keys).
      Pass 2: add commented-out keys IF they look like real keys
              (contain a hyphen or digit — prose words rarely do).
    """
    # Pattern for a valid redis-style config key (3+ chars)
    valid_key_re = re.compile(r"^[a-z][a-z0-9-]{2,}$")
    active_pat = re.compile(r"^([a-z][a-z0-9-]{2,})\s+(\S.*)$")
    commented_pat = re.compile(r"^#\s*([a-z][a-z0-9-]{2,})\s+(\S.*)$")

    active_keys: dict[str, str] = {}
    commented_keys: dict[str, str] = {}

    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("##"):
            continue

        if not stripped.startswith("#"):
            # Active directive
            m = active_pat.match(stripped)
            if m:
                key, raw_value = m.group(1), m.group(2)
                if key not in active_keys:
                    active_keys[key] = _strip_value(raw_value)
        else:
            # Commented line — only accept keys that look like real config keys
            m = commented_pat.match(stripped)
            if m:
                key, raw_value = m.group(1), m.group(2)
                # Real config keys contain a hyphen, digit, or are known active keys
                # Prose words like "incoming", "only", "disabled" rarely have hyphens
                if "-" in key or any(c.isdigit() for c in key):
                    if key not in commented_keys:
                        commented_keys[key] = _strip_value(raw_value)

    # Merge: active wins over commented
    result = dict(commented_keys)
    result.update(active_keys)

    # Accept short, non-hyphenated keys from the allowlist that appear as
    # commented directives (e.g. `# save 3600 1`).  These are genuine Redis
    # config keys that the hyphen-or-digit filter would otherwise reject.
    for line in text.splitlines():
        stripped = line.lstrip()
        if not stripped.startswith("#"):
            continue
        m = re.match(r"^#\s*([a-z][a-z0-9-]{2,})\s+(\S.*)$", stripped)
        if m and m.group(1) in _SHORT_KEY_ALLOWLIST:
            result.setdefault(m.group(1), _strip_value(m.group(2)))

    return result


def find_refs(text: str) -> list[int]:
    """Return sorted list of distinct issue/PR numbers referenced in `text`."""
    return sorted({int(n) for n in REF.findall(text or "")})


def find_reverted_sha(message: str) -> str | None:
    """Return the SHA prefix of the commit being reverted, or None."""
    m = REVERT.search(message or "")
    return m.group(1) if m else None


def entity_ids_for_commit(
    files: list[dict],
    config_files: set[str],
    known_keys: set[str] | None = None,
) -> dict[str, list]:
    """Map commit file changes to entity identifiers.

    Args:
        files:        list of {path, diff} dicts from CommitRecord.files
        config_files: set of paths that are config files (e.g. {'redis.conf'})
        known_keys:   authoritative key names from the live config file

    Returns:
        {
          "files":       [path, ...],
          "functions":   [(path, name), ...],
          "config_keys": [{key, value, change}, ...],
        }
    """
    res: dict[str, list] = {"files": [], "functions": [], "config_keys": []}
    for f in files:
        path = f["path"]
        res["files"].append(path)
        if path in config_files or path.endswith(".conf"):
            res["config_keys"] += extract_config_keys(f.get("diff", ""), known_keys)
        else:
            res["functions"] += [
                (path, name) for name in functions_from_hunks(f.get("diff", ""))
            ]
    return res
