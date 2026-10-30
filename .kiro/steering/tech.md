---
inclusion: always
---
# Technology and conventions

## Stack
- Python 3.11+, FastAPI, Pydantic v2, pydantic-settings
- Neo4j AuraDB (Cypher 5), official `neo4j` Python driver, vector + full-text indexes
- PyDriller for git history, GitHub GraphQL API via httpx for PRs/issues
- sentence-transformers (all-MiniLM-L6-v2, 384 dims) for embeddings
- LLM behind `backend/app/llm/provider.py` (Anthropic default, Sarvam optional)
- React 18 + Vite + Neo4j NVL (`@neo4j-nvl/react`) for the UI
- pytest for tests

## Conventions
- Type hints everywhere; Pydantic models for every cross-module payload.
- No secrets in code. Read config only through `backend/app/config.py`.
- All Cypher lives in `backend/app/graph/` or `backend/app/retrieval/cypher.py`; use parameters, never string-format user input.
- Ingestion stages write JSONL to `data/cache/` so they are resumable and re-runnable offline.
- LLM calls: always request JSON, validate with Pydantic, retry once on parse failure, log prompt + response hash.
- Every new module gets at least one unit test in `backend/tests/`. Pure logic (confidence, supersession status resolution) must be testable without Neo4j or an LLM.
- Keep functions small; prefer pure functions for scoring and status logic.

## Commands
- `make setup`, `make schema`, `make ingest`, `make build`, `make supersede`, `make serve`, `make ui`, `make eval`, `make test`
