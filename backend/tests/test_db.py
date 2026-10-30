"""Unit tests for db.py — error-message wrapping only. No live Neo4j."""
import pytest
from unittest.mock import MagicMock, patch
from neo4j.exceptions import AuthError, ServiceUnavailable

from backend.app.graph.db import Neo4jDB


def _db_with_mock_run(side_effect) -> Neo4jDB:
    """Return a Neo4jDB whose run() raises the given exception."""
    db = Neo4jDB.__new__(Neo4jDB)  # skip __init__ (would need live driver)
    db.run = MagicMock(side_effect=side_effect)
    return db


def test_version_wraps_auth_error():
    db = _db_with_mock_run(AuthError("raw driver message"))
    with pytest.raises(AuthError, match="NEO4J_USER"):
        db.version()


def test_version_wraps_service_unavailable():
    db = _db_with_mock_run(ServiceUnavailable("raw driver message"))
    with pytest.raises(ServiceUnavailable, match="NEO4J_URI"):
        db.version()


def test_ping_returns_false_on_any_exception():
    db = _db_with_mock_run(RuntimeError("anything"))
    assert db.ping() is False


def test_ping_returns_true_when_run_succeeds():
    db = Neo4jDB.__new__(Neo4jDB)
    db.run = MagicMock(return_value=[{"ok": 1}])
    assert db.ping() is True
