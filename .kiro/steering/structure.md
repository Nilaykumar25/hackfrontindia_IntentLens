---
inclusion: always
---
# Repository structure

```
backend/app/
  config.py            settings from .env
  models.py            Pydantic models (threads, decisions, answers)
  main.py              FastAPI app (/ask, /entity/{id}/graph, /health)
  llm/provider.py      LLM + embedding abstraction
  ingestion/           git_ingest.py, github_ingest.py
  extraction/          entities.py (config keys, functions), decision_miner.py
  graph/               db.py, schema.cypher, loader.py
  reasoning/           supersession.py, confidence.py
  retrieval/           cypher.py (templates), graphrag.py (pipeline)
backend/tests/         unit tests
scripts/               apply_schema, ingest, build_graph, run_supersession, run_eval
eval/                  gold_questions.json, baseline_rag.py, metrics.py
frontend/              React + Vite UI
docs/                  architecture, evaluation, demo script, pitch outline
.kiro/specs/intentlens requirements.md, design.md, tasks.md
```
Pipeline order: ingest -> build_graph (entities + evidence + decisions) -> run_supersession -> serve -> eval.
