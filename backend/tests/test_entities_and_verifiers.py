from backend.app.extraction.decision_miner import verify_decision
from backend.app.extraction.entities import extract_config_keys, find_refs, functions_from_hunks
from backend.app.models import ExtractedDecision, Span
from backend.app.retrieval.graphrag import exact_candidates, select_governing, verify_claims


def test_hunk_functions():
    diff = "@@ -10,6 +10,7 @@ int syncWithMaster(client *c) {\n+x\n@@ -50,3 +51,3 @@ void replicationCron(void) {"
    assert functions_from_hunks(diff) == ["replicationCron", "syncWithMaster"]


def test_config_key_change():
    diff = "--- a/redis.conf\n+++ b/redis.conf\n-repl-backlog-size 1mb\n+repl-backlog-size 5mb"
    r = extract_config_keys(diff)
    assert r[0]["key"] == "repl-backlog-size" and r[0]["change"] == "CHANGE" and r[0]["value"] == "5mb"


def test_refs():
    assert find_refs("Fixes #123 and see #45") == [45, 123]


def test_verify_decision_drops_fabricated_quotes():
    d = ExtractedDecision(title="t", summary="s", spans=[Span(source_id="x", quote="not in source")])
    assert verify_decision(d, "some other text") is None
    d2 = ExtractedDecision(title="t", summary="s", spans=[Span(source_id="x", quote="Use  a backlog")])
    assert verify_decision(d2, "we should use a backlog of 1mb") is not None


def test_verify_decision_whitespace_normalised_pass():
    """A quote that differs only in whitespace/newlines from the source must pass."""
    source = "we need  a high backlog\nin order to avoid slow clients"
    quote  = "we need a high backlog in order to avoid slow clients"   # normalised
    d = ExtractedDecision(title="t", summary="s", spans=[Span(source_id="doc#L1", quote=quote)])
    result = verify_decision(d, source)
    assert result is not None, "Whitespace-normalised quote must be accepted"
    assert len(result.spans) == 1


def test_verify_decision_rejects_absent_quote():
    """A quote not present in the source at all must be rejected, dropping the decision."""
    source = "The backlog is 1mb for memory efficiency."
    quote  = "We decided because of performance concerns"   # invented — not in source
    d = ExtractedDecision(title="t", summary="s", spans=[Span(source_id="doc#L1", quote=quote)])
    assert verify_decision(d, source) is None, "Fabricated quote must be dropped"


def test_verify_claims_requires_valid_citation():
    claims = [{"text": "ok", "evidence": ["E1", "E9"]}, {"text": "bad", "evidence": ["E7"]}, {"text": "none", "evidence": []}]
    assert verify_claims(claims, {"E1", "E2"}) == [{"text": "ok", "evidence": ["E1"]}]


def test_select_governing_prefers_latest_live():
    rows = [{"decision": {"status": "SUPERSEDED", "decided_on": "2020"}},
            {"decision": {"status": "ACTIVE", "decided_on": "2022"}},
            {"decision": {"status": "ACTIVE", "decided_on": "2021"}}]
    gov, hist = select_governing(rows)
    assert gov["decision"]["decided_on"] == "2022" and len(hist) == 2


def test_exact_candidates():
    assert "repl-backlog-size" in exact_candidates("Why is repl-backlog-size 1mb?")
