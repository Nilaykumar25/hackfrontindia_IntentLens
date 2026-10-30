"""Unit tests for GraphRAG pipeline using fake Neo4jDB and fake LLM.

No live network calls. All queries are intercepted by a mock DB that
returns canned responses based on query content matching.
"""
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from backend.app.models import AnswerResponse, EvidenceItem, Factors
from backend.app.retrieval.graphrag import (
    GraphRAG,
    exact_candidates,
    keywords,
    select_governing,
    verify_claims,
)
from backend.app.reasoning import confidence as conf


# ══════════════════════════════════════════════════════════════════════════════
# Pure-logic tests (no mocks needed)
# ══════════════════════════════════════════════════════════════════════════════

def test_keywords_filters_stopwords():
    kws = keywords("Why is the replication backlog size 1mb by default?")
    assert "replication" in kws
    assert "backlog" in kws
    assert "why" not in kws
    assert "the" not in kws


def test_exact_candidates_finds_hyphenated():
    cands = exact_candidates("Why is repl-backlog-size set to 1mb?")
    assert "repl-backlog-size" in cands


def test_exact_candidates_finds_function_call():
    cands = exact_candidates("Why does replicationCron() run every second?")
    assert "replicationcron" in cands  # lowercased by the function


def test_exact_candidates_finds_file_extension():
    cands = exact_candidates("Why is replication.c structured this way?")
    assert "replication.c" in cands


def test_verify_claims_drops_uncited():
    claims = [
        {"text": "good claim", "evidence": ["E1"]},
        {"text": "bad claim no refs", "evidence": []},
        {"text": "bad claim wrong refs", "evidence": ["E99"]},
    ]
    result = verify_claims(claims, {"E1", "E2"})
    assert len(result) == 1
    assert result[0]["text"] == "good claim"


def test_verify_claims_strips_invalid_refs():
    claims = [{"text": "ok", "evidence": ["E1", "E9"]}]
    result = verify_claims(claims, {"E1"})
    assert result == [{"text": "ok", "evidence": ["E1"]}]


def test_verify_claims_empty():
    assert verify_claims([], {"E1"}) == []
    assert verify_claims(None, {"E1"}) == []


def test_select_governing_prefers_latest_live():
    rows = [
        {"decision": {"status": "SUPERSEDED", "decided_on": "2020", "id": "a"}},
        {"decision": {"status": "ACTIVE", "decided_on": "2022", "id": "b"}},
        {"decision": {"status": "ACTIVE", "decided_on": "2021", "id": "c"}},
    ]
    gov, hist = select_governing(rows)
    assert gov["decision"]["id"] == "b"
    assert len(hist) == 2


def test_select_governing_all_superseded():
    rows = [
        {"decision": {"status": "SUPERSEDED", "decided_on": "2020", "id": "a"}},
        {"decision": {"status": "REVERSED", "decided_on": "2021", "id": "b"}},
    ]
    gov, hist = select_governing(rows)
    assert gov is None
    assert len(hist) == 2


# ══════════════════════════════════════════════════════════════════════════════
# Fake DB and LLM
# ══════════════════════════════════════════════════════════════════════════════

class FakeDB:
    """Mock Neo4jDB that returns canned responses based on query content."""

    def __init__(self):
        self._responses: list[tuple[str, list[dict]]] = []

    def add_response(self, query_contains: str, rows: list[dict]) -> "FakeDB":
        self._responses.append((query_contains, rows))
        return self

    def run(self, query: str, **params: Any) -> list[dict]:
        q_lower = query.lower()
        # Match most specific (longest needle) first to avoid false matches
        for needle, rows in sorted(self._responses, key=lambda x: -len(x[0])):
            if needle in q_lower:
                return rows
        return []

    def run_batches(self, query: str, rows: list[dict], size: int = 500, key: str = "rows") -> None:
        pass


class FakeLLM:
    """Mock LLM that returns a canned JSON response."""

    def __init__(self, json_response: dict | None = None):
        self.provider = "fake"
        self.model = "fake-model"
        self._json = json_response or {"claims": [{"text": "The decision was made.", "evidence": ["E1"]}]}

    def complete(self, system: str, user: str, max_tokens: int = 1500, cache: bool = True) -> str:
        return "translated"

    def complete_json(self, system: str, user: str, max_tokens: int = 1500) -> dict:
        return self._json


# ══════════════════════════════════════════════════════════════════════════════
# Entity linking tests with FakeDB
# ══════════════════════════════════════════════════════════════════════════════

def test_link_entities_exact_match():
    db = FakeDB()
    db.add_response("tolower(e.name) in $names", [
        {"id": "config:repl-backlog-size", "name": "repl-backlog-size", "labels": ["ConfigKey", "Entity"], "score": 10.0},
    ])
    db.add_response("fulltext.querynodes", [])
    rag = GraphRAG(db, FakeLLM())
    ents = rag.link_entities("Why is repl-backlog-size 1mb?")
    assert len(ents) == 1
    assert ents[0]["id"] == "config:repl-backlog-size"


def test_link_entities_fulltext_fallback():
    db = FakeDB()
    # No exact match, fulltext returns results
    db.add_response("tolower(e.name) in $names", [])
    db.add_response("fulltext.querynodes", [
        {"id": "fn:src/replication.c::replicationCron", "name": "replicationCron", "labels": ["Function", "Entity"], "score": 3.5},
    ])
    rag = GraphRAG(db, FakeLLM())
    ents = rag.link_entities("Why does the replication cron run every second?")
    assert len(ents) >= 1


# ══════════════════════════════════════════════════════════════════════════════
# Vector fallback test
# ══════════════════════════════════════════════════════════════════════════════

def test_vector_fallback_above_threshold():
    db = FakeDB()
    db.add_response("vector.querynodes", [
        {"id": "dec1", "entity_ids": ["config:repl-backlog-size"], "score": 0.85},
    ])
    db.add_response("d.id in $ids", [
        {"decision": {"id": "dec1", "title": "Set backlog to 1mb", "status": "ACTIVE", "decided_on": "2020", "summary": "s", "rationale": "r", "explicit_rationale": True, "agreement": 0.9, "alternatives_rejected": []}, "entity_ids": ["config:repl-backlog-size"], "evidence": [], "people": [], "superseded_by": [], "supersedes": []}
    ])
    rag = GraphRAG(db, FakeLLM())
    rows, score = rag.vector_fallback([0.1] * 384)
    assert len(rows) == 1
    assert score == 0.85


def test_vector_fallback_below_threshold():
    db = FakeDB()
    db.add_response("vector.querynodes", [
        {"id": "dec1", "entity_ids": [], "score": 0.3},
    ])
    rag = GraphRAG(db, FakeLLM())
    rows, score = rag.vector_fallback([0.1] * 384)
    assert rows == []
    assert score == 0.0


# ══════════════════════════════════════════════════════════════════════════════
# Replacement promotion test
# ══════════════════════════════════════════════════════════════════════════════

def test_promote_replacements_fetches_replacement():
    db = FakeDB()
    # Initial rows: one superseded decision with a replacement
    superseded_row = {
        "decision": {"id": "old1", "title": "Old decision", "status": "SUPERSEDED", "decided_on": "2020", "summary": "s", "rationale": "r", "explicit_rationale": True, "agreement": 0.5, "alternatives_rejected": []},
        "entity_ids": ["config:repl-backlog-size"],
        "evidence": [],
        "people": [],
        "superseded_by": [{"id": "new1", "title": "New decision", "decided_on": "2022"}],
        "supersedes": [],
    }
    replacement_row = {
        "decision": {"id": "new1", "title": "New decision", "status": "ACTIVE", "decided_on": "2022", "summary": "s", "rationale": "r", "explicit_rationale": True, "agreement": 0.9, "alternatives_rejected": []},
        "entity_ids": ["config:repl-backlog-size"],
        "evidence": [],
        "people": [],
        "superseded_by": [],
        "supersedes": [],
    }
    db.add_response("d.id in $ids", [replacement_row])
    rag = GraphRAG(db, FakeLLM())
    rows, notes = rag.promote_replacements([superseded_row])
    assert len(rows) == 2  # original + replacement
    assert len(notes) == 1
    assert "superseded" in notes[0].lower()


# ══════════════════════════════════════════════════════════════════════════════
# Full answer test: answered path
# ══════════════════════════════════════════════════════════════════════════════

def test_answer_path_answered():
    db = FakeDB()
    # Entity linking
    db.add_response("tolower(e.name) in $names", [
        {"id": "config:repl-backlog-size", "name": "repl-backlog-size", "labels": ["ConfigKey", "Entity"], "score": 10.0},
    ])
    db.add_response("fulltext.querynodes", [])
    # Fetch decisions
    db.add_response("match (d:decision)-[:governs]->(e)", [
        {
            "decision": {"id": "d1", "title": "Set backlog to 1mb", "status": "ACTIVE", "decided_on": "2020-01-01", "summary": "Set repl-backlog-size to 1mb.", "rationale": "To enable partial resync.", "explicit_rationale": True, "agreement": 0.9, "alternatives_rejected": ["256kb"]},
            "entity_ids": ["config:repl-backlog-size"],
            "evidence": [{"id": "c1", "kind": "Commit", "url": "http://x", "date": "2020-01-01", "author": "antirez", "snippet": "We set backlog to 1mb.", "quote": ""}],
            "people": ["antirez"],
            "superseded_by": [],
            "supersedes": [],
        }
    ])
    # Drift count
    db.add_response("c.date > $after", [{"n": 0}])
    # Top contributor (not needed since people is set)
    db.add_response("count(distinct c) as commits", [])

    llm = FakeLLM({"claims": [{"text": "The backlog was set to 1mb to enable partial resync.", "evidence": ["E1"]}]})
    rag = GraphRAG(db, llm)
    resp = rag.answer("Why is repl-backlog-size 1mb?")
    assert resp.status == "answered"
    assert resp.decision is not None
    assert resp.decision["title"] == "Set backlog to 1mb"
    assert len(resp.evidence) >= 1
    assert resp.confidence is not None


def test_answer_path_refused_no_entities():
    db = FakeDB()
    # No entities found, no vector results
    db.add_response("tolower(e.name) in $names", [])
    db.add_response("fulltext.querynodes", [])
    db.add_response("vector.querynodes", [])
    # Refusal path queries
    db.add_response("left(c.message", [])
    db.add_response("comment_embedding", [])
    db.add_response("count(distinct c) as commits", [])

    rag = GraphRAG(db, FakeLLM())
    resp = rag.answer("Why is the sky blue?")
    assert resp.status == "refused"
    assert resp.refusal_reason is not None
    assert resp.confidence.label == "No answer"


def test_answer_path_refused_all_superseded():
    db = FakeDB()
    db.add_response("tolower(e.name) in $names", [
        {"id": "config:repl-backlog-size", "name": "repl-backlog-size", "labels": ["ConfigKey", "Entity"], "score": 10.0},
    ])
    db.add_response("fulltext.querynodes", [])
    # All decisions superseded, no replacement found
    db.add_response("match (d:decision)-[:governs]->(e)", [
        {
            "decision": {"id": "d1", "title": "Old", "status": "SUPERSEDED", "decided_on": "2020", "summary": "s", "rationale": "r", "explicit_rationale": True, "agreement": 0.5, "alternatives_rejected": []},
            "entity_ids": ["config:repl-backlog-size"],
            "evidence": [],
            "people": [],
            "superseded_by": [{"id": "d2", "title": "New", "decided_on": "2022"}],
            "supersedes": [],
        }
    ])
    # Replacement fetch returns nothing (replacement not in graph)
    db.add_response("d.id in $ids", [])
    # Refusal path
    db.add_response("left(c.message", [{"id": "c1", "message": "msg", "date": "2021", "author": "dev", "url": "http://x"}])
    db.add_response("comment_embedding", [])
    db.add_response("count(distinct c) as commits", [{"id": "dev", "name": "Dev", "commits": 5, "last_active": "2021"}])

    rag = GraphRAG(db, FakeLLM())
    resp = rag.answer("Why is repl-backlog-size 1mb?")
    # Should refuse because replacement not found
    assert resp.status == "refused"


def test_answer_superseded_promotes_replacement():
    """When best match is superseded, the replacement should be fetched and shown."""
    db = FakeDB()
    db.add_response("tolower(e.name) in $names", [
        {"id": "config:repl-backlog-size", "name": "repl-backlog-size", "labels": ["ConfigKey", "Entity"], "score": 10.0},
    ])
    db.add_response("fulltext.querynodes", [])
    # Old superseded decision
    old_row = {
        "decision": {"id": "d_old", "title": "Old approach", "status": "SUPERSEDED", "decided_on": "2018", "summary": "Old summary", "rationale": "Old rationale", "explicit_rationale": True, "agreement": 0.5, "alternatives_rejected": []},
        "entity_ids": ["config:repl-backlog-size"],
        "evidence": [],
        "people": [],
        "superseded_by": [{"id": "d_new", "title": "New approach", "decided_on": "2020"}],
        "supersedes": [],
    }
    db.add_response("match (d:decision)-[:governs]->(e)", [old_row])

    # Replacement fetch returns the new decision
    new_row = {
        "decision": {"id": "d_new", "title": "New approach", "status": "ACTIVE", "decided_on": "2020-01-01", "summary": "New summary.", "rationale": "New rationale.", "explicit_rationale": True, "agreement": 0.9, "alternatives_rejected": ["old"]},
        "entity_ids": ["config:repl-backlog-size"],
        "evidence": [{"id": "c2", "kind": "Commit", "url": "http://x", "date": "2020-01-01", "author": "antirez", "snippet": "New approach.", "quote": ""}],
        "people": ["antirez"],
        "superseded_by": [],
        "supersedes": [{"id": "d_old", "title": "Old approach", "decided_on": "2018"}],
    }
    db.add_response("d.id in $ids", [new_row])

    # Drift
    db.add_response("c.date > $after", [{"n": 0}])

    llm = FakeLLM({"claims": [{"text": "New approach was chosen.", "evidence": ["E1"]}]})
    rag = GraphRAG(db, llm)
    resp = rag.answer("Why is repl-backlog-size 1mb?")
    assert resp.status == "answered"
    assert resp.decision["title"] == "New approach"
    assert resp.superseded_notice is not None
    assert "superseded" in resp.superseded_notice.lower()


# ══════════════════════════════════════════════════════════════════════════════
# Integration tests (skipped unless Neo4j is available)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
def test_integration_answered():
    """Requires a live Neo4j with data loaded."""
    import os
    if not os.environ.get("NEO4J_URI"):
        pytest.skip("NEO4J_URI not set")

    from backend.app.graph.db import get_db
    from backend.app.llm.provider import get_llm
    rag = GraphRAG(get_db(), get_llm())
    resp = rag.answer("Why does Redis use an event-driven model for IO threads?")
    assert resp.status in ("answered", "refused")
    if resp.status == "answered":
        assert resp.decision is not None
        assert len(resp.evidence) > 0
        assert resp.confidence.label in ("High", "Medium", "Low")


@pytest.mark.integration
def test_integration_superseded():
    """Question whose best match is superseded."""
    import os
    if not os.environ.get("NEO4J_URI"):
        pytest.skip("NEO4J_URI not set")

    from backend.app.graph.db import get_db
    from backend.app.llm.provider import get_llm
    rag = GraphRAG(get_db(), get_llm())
    # "Avoid simultaneous RDB and AOF child process" was SUPERSEDED
    resp = rag.answer("Why does Redis avoid simultaneous RDB and AOF child processes?")
    if resp.status == "answered":
        # If answered, check supersession awareness
        assert resp.decision is not None
    # Even if refused, should not crash


@pytest.mark.integration
def test_integration_refused():
    """Unanswerable question must refuse."""
    import os
    if not os.environ.get("NEO4J_URI"):
        pytest.skip("NEO4J_URI not set")

    from backend.app.graph.db import get_db
    from backend.app.llm.provider import get_llm
    rag = GraphRAG(get_db(), get_llm())
    resp = rag.answer("Why did the Redis team choose to use sds instead of C strings?")
    assert resp.status == "refused"
    assert resp.refusal_reason is not None
    assert resp.confidence.label == "No answer"
