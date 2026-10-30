# Implementation Plan: IntentLens

Work top to bottom. Each task is small enough to finish and verify in one session. The repository already contains starter code for most modules; "implement" means complete, harden and test it.

- [x] 1. Environment and project bootstrap
  - Copy `.env.example` to `.env`, fill Neo4j, GitHub and LLM keys
  - Create venv, `pip install -r requirements.txt`, run `make test` (the pure-logic tests must pass)
  - _Requirements: 11.2_

- [x] 2. Connect to AuraDB and apply the schema
  - Verify `backend/app/graph/db.py` connects; implement `scripts/apply_schema.py` check output
  - Run `make schema`; confirm constraints and indexes via `SHOW INDEXES`
  - _Requirements: 4.1_

- [x] 3. Git history ingestion
  - Clone target repo into `data/repo`; finish `ingestion/git_ingest.py` (rename detection, hunk capture, resumable)
  - Run on the subsystem paths; confirm `data/cache/commits.jsonl` has records
  - _Requirements: 1.1, 1.4, 2.3_

- [x] 4. GitHub PR and issue ingestion
  - Finish `ingestion/github_ingest.py` GraphQL pagination, rate-limit handling, subsystem filtering
  - Confirm `data/cache/threads.jsonl` contains PRs with comments and linked issues
  - _Requirements: 1.2, 1.3, 1.4_

- [x] 5. In-repo document ingestion
  - Add Document extraction for design docs, README sections and config comments in the configured paths
  - _Requirements: 1.5_

- [x] 6. Config key extraction
  - Complete `extraction/entities.py` `extract_config_keys` and parse defaults from `redis.conf`
  - Unit tests for add/change/remove of a key in a diff
  - _Requirements: 2.1_

- [x] 7. Function mapping from diff hunks
  - Implement `functions_from_hunks`; optionally upgrade to tree-sitter for C and Python
  - _Requirements: 2.2_

- [x] 8. Reference linking
  - Implement `find_refs` and link commits and threads to PR/Issue nodes
  - _Requirements: 2.4_

- [x] 9. Load evidence layer into Neo4j
  - Implement `loader.load_commits`, `load_threads` (idempotent MERGE, batches of 500), persons
  - Verify counts with Cypher; re-run to confirm no duplicates
  - _Requirements: 4.2, 4.3_

- [x] 10. Load entity layer
  - `loader.load_entities`: File, Function, ConfigKey nodes with `Entity` label and MODIFIES edges
  - _Requirements: 2.1, 2.2, 4.2_

- [x] 11. LLM and embedding provider
  - Finish `llm/provider.py` (Anthropic + Sarvam), JSON repair retry, content-hash cache
  - _Requirements: 3.1, 11.3_

- [x] 12. Decision mining prompts
  - Tune `decision_miner.SYSTEM` prompt on 10 hand-picked threads; capture few-shot examples
  - _Requirements: 3.1, 3.3_

- [x] 13. Verification and agreement
  - Implement quote verification, drop unverifiable decisions, two-pass agreement score
  - Tests for `verify_decision` and `agreement_score`
  - _Requirements: 3.2, 3.4_

- [x] 14. Decision loading and embeddings
  - `loader.load_decisions`: Decision nodes, GOVERNS, EVIDENCED_BY{quote}, MADE_BY, embeddings
  - Run `make build` end to end on a 50-thread sample first, then the full subsystem
  - _Requirements: 3.5, 4.2_

- [x] 15. Structural supersession
  - Implement `find_reverts` and REVERTS edges; tests
  - _Requirements: 5.1_

- [x] 16. Semantic supersession
  - Implement `classify_pair` prompt and pair selection; store reason + confidence
  - _Requirements: 5.2_

- [x] 17. Temporal resolution and status
  - Finish `compute_statuses` and `run_supersession`; verify against 5 known supersession cases
  - _Requirements: 5.3, 5.4, 5.5_

- [x] 18. Entity linking
  - Implement full-text + vector linking in `retrieval/graphrag.py`; tests with 10 sample questions
  - _Requirements: 6.1_

- [x] 19. Cypher templates and evidence pack
  - Finish `retrieval/cypher.py` templates and evidence pack builder with stable IDs (E1, E2, ...)
  - _Requirements: 6.2_

- [x] 20. Grounded generation and citation verifier
  - Implement JSON claims output, drop claims lacking valid citations; tests
  - _Requirements: 6.3_

- [x] 21. Supersession-aware answers and person-to-ask
  - Governing-decision selection, superseded notice, top-contributor query
  - _Requirements: 6.4, 6.5_

- [x] 22. Confidence engine
  - Finish factor computation incl. drift query; tests for score and label boundaries
  - _Requirements: 7.1, 7.3_

- [x] 23. Refusal path
  - Refuse on no decision or low score; return last changers and closest discussions
  - _Requirements: 7.2_

- [x] 24. FastAPI endpoints
  - `/ask`, `/entity/{id}/graph`, `/health`; CORS; error handling; latency logging
  - _Requirements: 6.5, 11.1_

- [x] 25. Frontend scaffold
  - `cd frontend && npm install && npm run dev`; verify proxy to backend
  - _Requirements: 8.5_

- [x] 26. Chat and answer card
  - Question box, answer card with decision, evidence chain, person, confidence reasons
  - _Requirements: 8.1_

- [x] 27. Superseded and refusal states
  - Warning banner with link to replacement; distinct refusal view
  - _Requirements: 8.2, 8.3_

- [x] 28. Timeline and graph views
  - Evidence timeline; NVL graph with status colours; node click expands
  - _Requirements: 8.4_

- [x] 29. Gold set construction
  - Fill `eval/gold_questions.json`: 30 answerable, 10 unanswerable, 5+ supersession cases
  - _Requirements: 9.1_

- [x] 30. Baseline RAG
  - Finish `eval/baseline_rag.py` (vector-only over commit and comment text, same LLM)
  - _Requirements: 9.1_

- [x] 31. Metrics runner
  - Finish `eval/metrics.py` and `scripts/run_eval.py`; output Markdown table to `docs/EVALUATION_RESULTS.md`
  - _Requirements: 9.2_

- [x] 32. Tune weights and thresholds
  - Adjust confidence weights and REFUSAL_THRESHOLD using gold-set calibration
  - _Requirements: 7.1, 7.2_

- [x] 33. Hinglish support (stretch)
  - Question normalisation via Sarvam; answer in user's language
  - _Requirements: 10.1_

- [x] 34. Deploy
  - Backend on Render/Railway, frontend on Vercel, AuraDB hosted; set env vars; smoke test
  - _Requirements: 11.1_

- [x] 35. Demo hardening and pitch assets
  - Pre-warm the graph, record a fallback video, rehearse `docs/DEMO_SCRIPT.md`, fill `docs/PITCH_OUTLINE.md`
  - _Requirements: all_

- [x] 36. Stretch: GitHub App and VS Code hover
  - Answer "why?" in PR comments; hover shows governing decision
