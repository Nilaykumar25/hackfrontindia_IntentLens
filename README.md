# IntentLens (engine: IntentGraph)

**Connect code to the decisions that shaped it.**

IntentLens answers "why is the code like this?" for a real public repository. It ingests commits, pull requests, issues and design docs, builds a Neo4j knowledge graph (IntentGraph) of code entities, decisions, people and incidents, and answers with a cited chain of evidence. It flags superseded decisions, shows a confidence signal, and refuses when the graph has no answer.

Built for hackFront India · AI and Developer Tools · PS 01 · Neo4j track.

## Status of this repository
This is a **working starter scaffold**: architecture, graph schema, pipeline modules, API, UI, tests and evaluation harness are in place. The pure-logic modules (confidence, supersession status resolution, verifiers, entity parsing) are unit-tested. The parts that need live services (AuraDB, GitHub, an LLM key) have **not** been run end to end yet. Completing, running and hardening them is the job of the Kiro task list in `.kiro/specs/intentlens/tasks.md`; start with `KIRO_PROMPT.md`.

## Quick start
```bash
cp .env.example .env              # fill Neo4j, GitHub token, LLM key
make setup && source .venv/bin/activate
make test                         # 17 unit tests, no services needed
make schema                       # create constraints and indexes in AuraDB
make ingest                       # clone repo, cache commits + PRs
python -m scripts.build_graph --limit 50   # sample run first
make build                        # full load + decision mining
make supersede                    # supersession engine
make serve                        # API on :8000
make ui                           # UI on :5173
make eval                         # IntentLens vs vector-RAG baseline
```

## Layout
See `.kiro/steering/structure.md`. Architecture: `docs/ARCHITECTURE.md`. Demo: `docs/DEMO_SCRIPT.md`. Pitch: `docs/PITCH_OUTLINE.md`. Evaluation method: `docs/EVALUATION.md`. AuraDB setup: `docs/SETUP_AURADB.md`.

## Known limitations (be upfront in the pitch)
- Commit authors are keyed by email and PR authors by GitHub login, so one human can appear as two Person nodes until an identity-mapping step is added.
- Dates are stored as ISO strings; mixed timezone formats can mis-order edge cases.
- Function mapping uses git hunk headers (good for C and Python, approximate elsewhere); tree-sitter is the upgrade path.
- The Sarvam adapter targets an OpenAI-style endpoint; verify the endpoint and model name against Sarvam's current docs.
- The `@neo4j-nvl/react` API and version should be checked against the current NVL docs when you run `npm install`.
