"""Tests for Stage 0 UI backend additions: /stats, /entities/search, /eval/results."""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


# ── /stats ─────────────────────────────────────────────────────────────────────

def test_stats_returns_expected_shape():
    with patch("backend.app.main.get_db") as mock:
        mock_db = MagicMock()
        mock_db.run.return_value = [{
            "commits": 1372, "decisions": 64, "superseded": 5, "persons": 249, "entities": 467,
        }]
        mock.return_value = mock_db
        r = client.get("/stats")
        assert r.status_code == 200
        data = r.json()
        assert set(data.keys()) == {"commits", "decisions", "superseded", "persons", "entities"}
        assert data["commits"] == 1372
        assert data["decisions"] == 64


def test_stats_returns_zeros_on_db_error():
    with patch("backend.app.main.get_db") as mock:
        mock_db = MagicMock()
        mock_db.run.side_effect = RuntimeError("db down")
        mock.return_value = mock_db
        r = client.get("/stats")
        assert r.status_code == 200
        data = r.json()
        assert all(v == 0 for v in data.values())


def test_stats_returns_zeros_on_empty_result():
    with patch("backend.app.main.get_db") as mock:
        mock_db = MagicMock()
        mock_db.run.return_value = []
        mock.return_value = mock_db
        r = client.get("/stats")
        assert r.status_code == 200
        assert all(v == 0 for v in r.json().values())


# ── /entities/search ──────────────────────────────────────────────────────────

def test_entities_search_returns_list():
    with patch("backend.app.main.get_db") as mock:
        mock_db = MagicMock()
        mock_db.run.return_value = [
            {"id": "config:repl-backlog-size", "name": "repl-backlog-size", "labels": ["ConfigKey", "Entity"], "score": 5.0},
            {"id": "fn:src/replication.c::replicationCron", "name": "replicationCron", "labels": ["Function", "Entity"], "score": 3.0},
        ]
        mock.return_value = mock_db
        r = client.get("/entities/search", params={"q": "repl"})
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2
        assert data[0]["id"] == "config:repl-backlog-size"
        assert data[0]["type"] == "ConfigKey"


def test_entities_search_empty_query_returns_empty():
    r = client.get("/entities/search", params={"q": ""})
    assert r.status_code == 200
    assert r.json() == []


def test_entities_search_query_too_long():
    r = client.get("/entities/search", params={"q": "x" * 101})
    assert r.status_code == 400


def test_entities_search_returns_empty_on_db_error():
    with patch("backend.app.main.get_db") as mock:
        mock_db = MagicMock()
        mock_db.run.side_effect = RuntimeError("fulltext index missing")
        mock.return_value = mock_db
        r = client.get("/entities/search", params={"q": "test"})
        assert r.status_code == 200
        assert r.json() == []


# ── /eval/results ─────────────────────────────────────────────────────────────

SAMPLE_MD = """# Evaluation Results

## Calibration Check

- Mean confidence (correct answers): **0.474**
- Mean confidence (incorrect answers): **0.091**

## Dev Split (Keyword)

| Metric | Vector-RAG baseline | IntentLens |
|---|---|---|
| answer_accuracy | 0.8 | 0.75 |
| refusal_correctness | 0.0 | 1.0 |

## Held-Out Split (Keyword)

| Metric | Vector-RAG baseline | IntentLens |
|---|---|---|
| answer_accuracy | 1.0 | 0.2 |
| refusal_correctness | 0.0 | 1.0 |
"""


def test_eval_results_parses_markdown():
    """Write a temp MD to the actual path the endpoint reads, then restore it."""
    path = "docs/EVALUATION_RESULTS.md"
    # Back up existing file if present
    backup = None
    if os.path.exists(path):
        backup = open(path, encoding="utf-8").read()

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(SAMPLE_MD)

        r = client.get("/eval/results")
        assert r.status_code == 200
        data = r.json()
        assert "dev" in data
        assert "held_out" in data
        assert "calibration" in data
        assert data["calibration"]["mean_conf_correct"] == 0.474
        assert data["dev"]["answer_accuracy"]["intentlens"] == 0.75
        assert data["dev"]["refusal_correctness"]["baseline"] == 0.0
    finally:
        if backup is not None:
            with open(path, "w", encoding="utf-8") as f:
                f.write(backup)
        elif os.path.exists(path):
            os.unlink(path)


def test_eval_results_404_when_file_missing():
    with patch("backend.app.main.os.path.exists", return_value=False):
        r = client.get("/eval/results")
        assert r.status_code == 404
        assert "make eval" in r.json()["detail"]["message"].lower()
