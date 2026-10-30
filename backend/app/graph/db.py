from __future__ import annotations

import sys
from typing import Any

from neo4j import GraphDatabase
from neo4j.exceptions import AuthError, ServiceUnavailable

from ..config import settings


class Neo4jDB:
    def __init__(self) -> None:
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    def run(self, query: str, **params: Any) -> list[dict]:
        try:
            with self.driver.session(database=settings.neo4j_database) as s:
                return [r.data() for r in s.run(query, **params)]
        except Exception:
            # Reconnect once on transient connection errors (AuraDB serverless idle timeout)
            self.driver = GraphDatabase.driver(
                settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
            )
            with self.driver.session(database=settings.neo4j_database) as s:
                return [r.data() for r in s.run(query, **params)]

    def run_batches(self, query: str, rows: list[dict], size: int = 500, key: str = "rows") -> None:
        for i in range(0, len(rows), size):
            self.run(query, **{key: rows[i : i + size]})

    def ping(self) -> bool:
        """Return True if the database is reachable; False otherwise."""
        try:
            self.run("RETURN 1 AS ok")
            return True
        except Exception:
            return False

    def version(self) -> str:
        """Return the server version string, e.g. '5.26.0'.

        Raises AuthError / ServiceUnavailable with a human-readable message
        so callers can surface clear diagnostics.
        """
        try:
            rows = self.run(
                "CALL dbms.components() YIELD name, versions "
                "WHERE name = 'Neo4j Kernel' RETURN versions[0] AS ver"
            )
            return rows[0]["ver"] if rows else "unknown"
        except AuthError as exc:
            raise AuthError(
                f"Neo4j authentication failed for user '{settings.neo4j_user}' "
                f"at {settings.neo4j_uri!r}. "
                "Check NEO4J_USER and NEO4J_PASSWORD in your .env file."
            ) from exc
        except ServiceUnavailable as exc:
            raise ServiceUnavailable(
                f"Cannot reach Neo4j at {settings.neo4j_uri!r}. "
                "Check NEO4J_URI in your .env and that the AuraDB instance is running."
            ) from exc

    def close(self) -> None:
        self.driver.close()


_db: Neo4jDB | None = None


def get_db() -> Neo4jDB:
    global _db
    if _db is None:
        _db = Neo4jDB()
    return _db


def reset_db() -> None:
    """Force the singleton to recreate the driver on next get_db() call."""
    global _db
    if _db is not None:
        try:
            _db.close()
        except Exception:
            pass
    _db = None
