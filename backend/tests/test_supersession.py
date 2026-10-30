from backend.app.reasoning.supersession import Link, compute_statuses, find_reverts


def test_contradiction_supersedes_older():
    s = compute_statuses(["a", "b"], [Link("b", "a", "SUPERSEDES", 0.9)])
    assert s == {"a": "SUPERSEDED", "b": "ACTIVE"}


def test_low_confidence_is_uncertain():
    assert compute_statuses(["a", "b"], [Link("b", "a", "SUPERSEDES", 0.4)])["a"] == "UNCERTAIN"


def test_revert_beats_supersede():
    s = compute_statuses(["a", "b", "c"], [Link("b", "a", "SUPERSEDES", 0.9), Link("c", "a", "REVERTS", 0.95)])
    assert s["a"] == "REVERSED"


def test_refines_keeps_active():
    assert compute_statuses(["a", "b"], [Link("b", "a", "REFINES", 0.9)])["a"] == "ACTIVE"


def test_find_reverts():
    commits = [{"sha": "bbb", "message": "Revert x\n\nThis reverts commit abc1234def."}, {"sha": "ccc", "message": "normal"}]
    assert find_reverts(commits) == [("bbb", "abc1234def")]
