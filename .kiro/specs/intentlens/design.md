# Design Document: IntentLens

## Overview
Four layers: ingestion, IntentGraph (Neo4j), reasoning (decision mining, supersession, confidence), and experience (FastAPI + React). All retrieval is graph-first: entity linking -> guarded Cypher traversal -> evidence pack -> grounded generation -> citation verification -> confidence/refusal.

```
GitHub/git --> ingestion (JSONL cache) --> entity extraction --> loader --> Neo4j
                                                |                          ^
                                         decision miner (LLM) -------------|
                                                |
                                      supersession engine (3 signals)
Question --> link entities --> Cypher templates --> evidence pack --> LLM --> verifier --> confidence --> answer | refusal
```

## Graph schema
Labels: `Entity` (secondary label on File, Module, Function, ConfigKey), `Commit`, `PullRequest`, `Issue`, `Comment`, `Document`, `Decision`, `Person`, `Incident`.

| Node | Key properties |
|---|---|
| File | id=path, name, path |
| Function | id="fn:{path}::{name}", name, path |
| ConfigKey | id="config:{key}", name, default_value, file |
| Commit | id=sha, message, date, url, text |
| PullRequest / Issue | id="pr:{n}" / "issue:{n}", number, title, body, url, created_at, text |
| Comment | id, author, created_at, url, text |
| Document | id=path, text |
| Decision | id, title, summary, rationale, alternatives_rejected, decided_on, status, explicit_rationale, agreement, embedding |
| Person | id=login or email, name |
| Incident | id, title, severity, date |

Relationships: MODIFIES, PART_OF, CLOSES, REFERENCES, AUTHORED, COMMENTED_ON, GOVERNS, EVIDENCED_BY{quote}, MADE_BY, SUPERSEDES{reason,confidence}, REFINES, REVERTS, TRIGGERED.
Convention: `(newer)-[:SUPERSEDES]->(older)`; `(newer)-[:REVERTS]->(older)`.

## Components and interfaces

### ingestion
- `git_ingest.ingest_commits(repo_path, paths, out_path)` -> JSONL of `CommitRecord`.
- `github_ingest.ingest_prs(owner, repo, paths, out_path, max_prs)` -> JSONL of `Thread` (kind=pr) with comments, reviews, commits, closing issues, files.
- Both are resumable (skip ids already in the output file).

### extraction
- `entities.extract_config_keys(diff_or_text)` -> list[(key, value|None, change)].
- `entities.functions_from_hunks(diff)` -> function names from git hunk headers (tree-sitter optional upgrade).
- `entities.find_refs(text)` -> issue/PR numbers.
- `decision_miner.mine_thread(llm, thread)` -> list[ExtractedDecision]; `verify_decision` enforces quote presence; `agreement_score` compares two passes by embedding similarity.

### graph
- `db.Neo4jDB.run(query, **params)`; `schema.cypher` applied by `scripts/apply_schema.py`.
- `loader.py` exposes `load_commits`, `load_threads`, `load_entities`, `load_decisions` using UNWIND + MERGE in batches of 500.

### reasoning
- `supersession.find_reverts(commits)`; `supersession.classify_pair(llm, older, newer)`; pure `compute_statuses(ids, links, min_conf)`; `run_supersession(db, llm)` persists edges and statuses.
- `confidence.Factors`, `confidence.score(factors)`, `confidence.label(score, has_decision)`.

### retrieval
- `cypher.py`: templates `DECISIONS_BY_ENTITY`, `LAST_CHANGERS`, `TOP_CONTRIBUTOR`, `RELATED_DISCUSSIONS`, `DRIFT_COUNT`, `NEIGHBOURHOOD`.
- `graphrag.GraphRAG.answer(question, lang)` -> `AnswerResponse`.

### API
- `POST /ask {question, lang?}` -> `AnswerResponse`
- `GET /entity/graph?id={id}` -> `{nodes, rels}` (query param; entity ids contain slashes/colons, making path params awkward)
- `GET /health` -> `{status, neo4j, llm}`

## Data models (Pydantic)
`CommitRecord`, `Thread`, `Comment`, `Span`, `ExtractedDecision`, `Factors`, `Confidence`, `EvidenceItem`, `AnswerResponse` (see `backend/app/models.py`).

## Confidence model
score = 0.30*directness + 0.25*corroboration + 0.20*agreement + 0.15*currency + 0.10*distance
- directness: 1.0 explicit rationale, 0.5 inferred
- corroboration: distinct independent evidence sources 1 -> 0.4, 2 -> 0.7, 3+ -> 1.0
- agreement: stored two-pass agreement
- currency: 1 - min(1, drift_commits/5), drift = later commits touching the entity with no later decision
- distance: 1 - (hops-1)/MAX_GRAPH_HOPS
Labels: >=0.75 High, >=0.55 Medium, >=REFUSAL_THRESHOLD Low, else No answer. Weights tuned on gold set.

## Supersession algorithm
1. Structural: parse "This reverts commit <sha>" and `Revert "..."`; link decisions evidenced by the commits.
2. Semantic: per entity, order decisions by date; classify consecutive and non-adjacent pairs where titles/embeddings are similar.
3. Temporal: `compute_statuses` applies precedence SUPERSEDED/REVERSED > UNCERTAIN > ACTIVE.

## Error handling
- LLM JSON parse failure: retry once with a repair instruction, then skip item and log.
- GitHub rate limits: sleep until reset header.
- Neo4j transient errors: retry with backoff (driver built-in).
- Empty retrieval: refusal path, never an LLM guess.

## Testing strategy
- Unit: confidence, compute_statuses, find_reverts, find_refs, config key parsing, citation verifier.
- Integration (optional, needs AuraDB): load 20 commits and 5 threads, ask 3 questions.
- Evaluation: `scripts/run_eval.py` against `eval/gold_questions.json`.

## Security and cost
- LLM never sees secrets; Cypher is parameterised; cache extractions by content hash to control cost.
