"""API tests using FastAPI TestClient with mocked DB and LLM.

These tests patch get_db and GraphRAG.answer to avoid live Neo4j/LLM calls.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


# ── Health and ready endpoints ─────────────────────────────────────────────────

def test_health_returns_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ready_returns_neo4j_status():
    with patch("backend.app.main.get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_db.ping.return_value = True
        mock_get_db.return_value = mock_db
        r = client.get("/ready")
        assert r.status_code == 200
        data = r.json()
        assert data["neo4j"] is True
        assert data["llm"]["provider"] is not None


def test_ready_degraded_when_neo4j_down():
    with patch("backend.app.main.get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_db.ping.return_value = False
        mock_get_db.return_value = mock_db
        r = client.get("/ready")
        assert r.status_code == 200
        assert r.json()["status"] == "degraded"


# ── Ask endpoint ──────────────────────────────────────────────────────────────

def _mock_answer(status="answered"):
    """Return a mock AnswerResponse dict."""
    return {
        "question": "test question",
        "status": status,
        "answer": "test answer [E1]",
        "decision": {"id": "d1", "title": "Test Decision", "status": "ACTIVE", "decided_on": "2020-01-01"},
        "superseded_notice": None,
        "replaced_by": None,
        "evidence": [{"ref": "E1", "id": "c1", "kind": "Commit", "url": "http://x", "date": "2020-01-01", "author": "antirez", "snippet": "test", "quote": ""}],
        "person_to_ask": {"id": "antirez", "name": "antirez", "reason": "Made this decision"},
        "history": [],
        "confidence": {"score": 0.7, "label": "Medium", "factors": None, "reasons": ["test reason"]},
        "refusal_reason": None,
        "related": [],
        "graph": {"nodes": [], "rels": []},
        "latency_ms": 100,
    }


def test_ask_valid_question():
    from backend.app.models import AnswerResponse, Confidence
    mock_resp = AnswerResponse(
        question="Why is repl-backlog-size 1mb?",
        status="answered",
        answer="test answer [E1]",
        decision={"id": "d1", "title": "Test", "status": "ACTIVE", "decided_on": "2020"},
        evidence=[],
        confidence=Confidence(score=0.7, label="Medium", reasons=["test"]),
        latency_ms=100,
    )
    with patch("backend.app.main.GraphRAG") as mock_rag_class:
        mock_rag = MagicMock()
        mock_rag.answer.return_value = mock_resp
        mock_rag_class.return_value = mock_rag
        r = client.post("/ask", json={"question": "Why is repl-backlog-size 1mb?"})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "answered"
        assert "answer" in data


def test_ask_empty_question_rejected():
    r = client.post("/ask", json={"question": ""})
    assert r.status_code == 422  # Pydantic validation error


def test_ask_short_question_rejected():
    r = client.post("/ask", json={"question": "ab"})
    assert r.status_code == 422  # min_length=3


def test_ask_long_question_rejected():
    r = client.post("/ask", json={"question": "x" * 501})
    assert r.status_code == 422  # max_length=500


def test_ask_invalid_lang_rejected():
    r = client.post("/ask", json={"question": "test question", "lang": "fr"})
    assert r.status_code == 422  # pattern validation


def test_ask_refused_returns_refused_status():
    from backend.app.models import AnswerResponse, Confidence
    mock_resp = AnswerResponse(
        question="Why is the sky blue?",
        status="refused",
        refusal_reason="No decision found",
        confidence=Confidence(score=0.0, label="No answer", reasons=["No decision found"]),
        latency_ms=50,
    )
    with patch("backend.app.main.GraphRAG") as mock_rag_class:
        mock_rag = MagicMock()
        mock_rag.answer.return_value = mock_resp
        mock_rag_class.return_value = mock_rag
        r = client.post("/ask", json={"question": "Why is the sky blue?"})
        assert r.status_code == 200
        assert r.json()["status"] == "refused"


def test_ask_internal_error_returns_500():
    with patch("backend.app.main.GraphRAG") as mock_rag_class:
        mock_rag = MagicMock()
        mock_rag.answer.side_effect = RuntimeError("DB connection lost")
        mock_rag_class.return_value = mock_rag
        r = client.post("/ask", json={"question": "test question"})
        assert r.status_code == 500
        assert "error" in r.json()["detail"]


# ── Entity graph endpoint ──────────────────────────────────────────────────────

def test_entity_graph_valid():
    with patch("backend.app.main.get_db") as mock_get_db:
        mock_db = MagicMock()
        # First call = NEIGHBOURHOOD query, second call = supersession query (returns [])
        neighbourhood_row = [
            {"eid": "config:repl-backlog-size", "ename": "repl-backlog-size",
             "d": {"id": "d1", "title": "Set backlog", "status": "ACTIVE"},
             "rtype": "GOVERNS", "outgoing": True, "xid": None, "xlabel": None, "xname": None},
        ]
        mock_db.run.side_effect = [neighbourhood_row, []]  # NEIGHBOURHOOD then supersession
        mock_get_db.return_value = mock_db
        r = client.get("/entity/graph", params={"id": "config:repl-backlog-size"})
        assert r.status_code == 200
        data = r.json()
        assert len(data["nodes"]) >= 2
        assert len(data["rels"]) >= 1


def test_entity_graph_empty_id_rejected():
    r = client.get("/entity/graph", params={"id": ""})
    assert r.status_code == 400


def test_entity_graph_no_results():
    with patch("backend.app.main.get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_db.run.side_effect = [[], []]  # NEIGHBOURHOOD empty, supersession empty
        mock_get_db.return_value = mock_db
        r = client.get("/entity/graph", params={"id": "nonexistent"})
        assert r.status_code == 200
        assert r.json() == {"nodes": [], "rels": []}


# ── /entity/graph?expand= endpoint ────────────────────────────────────────────

def test_entity_graph_with_expand():
    """?expand= causes a second NEIGHBOURHOOD query; nodes from both are merged."""
    with patch("backend.app.main.get_db") as mock_get_db:
        mock_db = MagicMock()
        base_row = [
            {"eid": "config:repl-backlog-size", "ename": "repl-backlog-size",
             "d": {"id": "d1", "title": "Set backlog", "status": "ACTIVE"},
             "rtype": "GOVERNS", "outgoing": True, "xid": None, "xlabel": None, "xname": None},
        ]
        expand_row = [
            {"eid": "config:appenddirname", "ename": "appenddirname",
             "d": {"id": "d2", "title": "Multi-Part AOF", "status": "ACTIVE"},
             "rtype": "GOVERNS", "outgoing": True, "xid": None, "xlabel": None, "xname": None},
        ]
        # calls: NEIGHBOURHOOD(id), supersession, NEIGHBOURHOOD(expand)
        mock_db.run.side_effect = [base_row, [], expand_row]
        mock_get_db.return_value = mock_db
        r = client.get("/entity/graph", params={
            "id": "config:repl-backlog-size",
            "expand": "config:appenddirname",
        })
        assert r.status_code == 200
        data = r.json()
        node_ids = {n["id"] for n in data["nodes"]}
        assert "d1" in node_ids
        assert "d2" in node_ids


def test_entity_graph_review_flag_on_edge():
    """Supersession edges with review_flag must appear in rels."""
    with patch("backend.app.main.get_db") as mock_get_db:
        mock_db = MagicMock()
        neighbourhood_row = [
            {"eid": "config:bind", "ename": "bind",
             "d": {"id": "d1", "title": "Bind default", "status": "SUPERSEDED"},
             "rtype": "GOVERNS", "outgoing": True, "xid": None, "xlabel": None, "xname": None},
        ]
        sup_row = [
            {"nid": "d2", "oid": "d1", "rtype": "SUPERSEDES",
             "conf": 1.0, "reason": "default changed", "review_flag": ""},
            {"nid": "d3", "oid": "d2", "rtype": "REFINES",
             "conf": 0.9, "reason": "comment out", "review_flag": "needs_review"},
        ]
        mock_db.run.side_effect = [neighbourhood_row, sup_row]
        mock_get_db.return_value = mock_db
        r = client.get("/entity/graph", params={"id": "config:bind"})
        assert r.status_code == 200
        data = r.json()
        sup_rels = [rel for rel in data["rels"] if rel["type"] in ("SUPERSEDES", "REFINES")]
        assert len(sup_rels) == 2
        flagged = [rel for rel in sup_rels if rel.get("review_flag") == "needs_review"]
        assert len(flagged) == 1


# ── /stats endpoint ────────────────────────────────────────────────────────────

def test_stats_valid():
    """GET /stats returns graph counts."""
    with patch("backend.app.main.get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_db.run.return_value = [{
            "commits": 1372, "decisions": 570, "superseded": 14,
            "persons": 554, "entities": 508,
        }]
        mock_get_db.return_value = mock_db
        r = client.get("/stats")
        assert r.status_code == 200
        data = r.json()
        assert data["commits"] == 1372
        assert data["decisions"] == 570
        assert "entities" in data


# ── /entities/search endpoint ──────────────────────────────────────────────────

def test_entities_search_valid():
    """GET /entities/search?q= returns list of entity dicts."""
    with patch("backend.app.main.get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_db.run.return_value = [
            {"id": "config:repl-backlog-size", "name": "repl-backlog-size",
             "labels": ["ConfigKey", "Entity"], "score": 9.5},
        ]
        mock_get_db.return_value = mock_db
        r = client.get("/entities/search", params={"q": "repl-backlog"})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert data[0]["id"] == "config:repl-backlog-size"
        assert data[0]["type"] == "ConfigKey"


def test_entities_search_empty_q():
    r = client.get("/entities/search", params={"q": ""})
    assert r.status_code == 200
    assert r.json() == []


def test_entities_search_long_q():
    r = client.get("/entities/search", params={"q": "x" * 101})
    assert r.status_code == 400


# ── /eval/results endpoint ─────────────────────────────────────────────────────

def test_eval_results_404_when_missing(tmp_path):
    """Returns 404 when EVALUATION_RESULTS.md does not exist."""
    import os
    # Ensure the docs dir file doesn't exist in the test path context
    # The endpoint reads "docs/EVALUATION_RESULTS.md" relative to cwd
    # We just test with a non-existent state by patching os.path.exists
    with patch("os.path.exists", return_value=False):
        r = client.get("/eval/results")
        assert r.status_code == 404


def test_eval_results_returns_structured_data(tmp_path):
    """Returns parsed dict when the markdown file exists and has content."""
    import os, builtins

    sample_md = """# Evaluation Results

## Dev Split

| Metric | Baseline | IntentLens |
|--------|----------|------------|
| answer_accuracy | 0.40 | 0.75 |
| refusal_correctness | 0.00 | 0.80 |

Mean confidence (correct answers): **0.72**
Mean confidence (incorrect answers): **0.35**
"""
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", MagicMock(return_value=__import__('io').StringIO(sample_md))):
        r = client.get("/eval/results")
        assert r.status_code == 200
        data = r.json()
        assert "dev" in data
        assert data["calibration"]["mean_conf_correct"] == 0.72
