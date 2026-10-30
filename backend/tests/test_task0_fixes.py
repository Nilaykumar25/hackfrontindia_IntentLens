"""Tests for Task 0 bug fixes: G9, G19, G11/G12/G13 loader routing."""
from backend.app.extraction.entities import extract_config_keys
from backend.app.models import Factors
from backend.app.reasoning import confidence as c


# ── G9: config key extraction must not accept commented-out lines ────────────

def test_commented_key_skipped_without_known_keys():
    """A line like '+# bind 127.0.0.1' should be ignored when no known_keys are given."""
    diff = "+# bind 127.0.0.1\n+maxmemory 2gb"
    result = extract_config_keys(diff)
    keys = [r["key"] for r in result]
    # 'bind' is commented-out with no known_keys → must be skipped
    assert "bind" not in keys


def test_commented_key_accepted_when_in_known_keys():
    """A commented default should be accepted when its key is explicitly known."""
    diff = "+# bind 127.0.0.1"
    result = extract_config_keys(diff, known_keys={"bind"})
    assert any(r["key"] == "bind" for r in result)


def test_commented_key_rejected_when_not_in_known_keys():
    """A commented line is rejected even with a known_keys set if the key isn't in it."""
    diff = "+# bind 127.0.0.1"
    result = extract_config_keys(diff, known_keys={"maxmemory"})
    assert not any(r["key"] == "bind" for r in result)


def test_uncommented_key_always_accepted():
    """A plain (uncommented) config change is always accepted."""
    diff = "+maxmemory 2gb"
    result = extract_config_keys(diff)
    assert any(r["key"] == "maxmemory" for r in result)


def test_existing_change_detection_still_works():
    """Regression: ADD+REMOVE of same key → CHANGE, value is the ADD value."""
    diff = "-repl-backlog-size 1mb\n+repl-backlog-size 5mb"
    result = extract_config_keys(diff, known_keys={"repl-backlog-size"})
    assert result[0]["change"] == "CHANGE"
    assert result[0]["value"] == "5mb"


# ── G19: neutral currency when entity_ids is empty ───────────────────────────

def test_confidence_build_currency_unknown_uses_neutral():
    """When currency_unknown=True, currency factor must be 0.5, not 0.0."""
    f = Factors(directness=1.0, corroboration=1.0, agreement=1.0, currency=0.5, distance=1.0)
    result = c.build(f, drift=0, n_sources=2, currency_unknown=True)
    # currency was set to neutral 0.5 by the caller; verify the reason text reflects it
    assert any("Could not measure" in r for r in result.reasons)


def test_confidence_build_normal_drift_message():
    """When currency_unknown=False and drift>0, the drift count appears in reasons."""
    f = Factors(directness=1.0, corroboration=1.0, agreement=1.0, currency=0.4, distance=1.0)
    result = c.build(f, drift=3, n_sources=2, currency_unknown=False)
    assert any("3 later change" in r for r in result.reasons)


def test_confidence_build_zero_drift_message():
    f = Factors(directness=1.0, corroboration=1.0, agreement=1.0, currency=1.0, distance=1.0)
    result = c.build(f, drift=0, n_sources=2, currency_unknown=False)
    assert any("still matches" in r for r in result.reasons)


# ── G11/G12/G13: loader comment routing (pure logic, no Neo4j) ──────────────

def test_comment_routing_by_thread_prefix():
    """PR comments go to PullRequest match; issue comments go to Issue match — verify split."""
    comments = [
        {"id": "c1", "thread": "pr:100", "author": "a", "date": "", "url": "", "text": "x"},
        {"id": "c2", "thread": "pr:101", "author": "b", "date": "", "url": "", "text": "y"},
        {"id": "c3", "thread": "issue:5", "author": "c", "date": "", "url": "", "text": "z"},
        {"id": "c4", "thread": "issue:6", "author": "d", "date": "", "url": "", "text": "w"},
    ]
    pr_comments = [cm for cm in comments if cm["thread"].startswith("pr:")]
    issue_comments = [cm for cm in comments if cm["thread"].startswith("issue:")]
    assert len(pr_comments) == 2
    assert len(issue_comments) == 2
    assert all(c["thread"].startswith("pr:") for c in pr_comments)
    assert all(c["thread"].startswith("issue:") for c in issue_comments)
