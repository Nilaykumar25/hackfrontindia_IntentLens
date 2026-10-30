# KIRO_PROMPT.md: how to build IntentLens in Kiro, step by step

This file gives you (1) one-time setup, (2) a kickoff prompt, (3) one copy-paste prompt per phase, in the exact order to run them, (4) recovery prompts. Menu labels in Kiro can change between versions; the ideas stay the same.

The repository already contains a starter scaffold and a Kiro spec (`.kiro/specs/intentlens/`: requirements, design, tasks) plus steering files (`.kiro/steering/`: product, tech, structure). Kiro reads steering automatically, so you do not need to repeat project context in every prompt.

---

## Part 1: One-time setup (30 to 45 minutes)

1. **Install prerequisites:** Python 3.11+, Node 18+, Git. Install Kiro and sign in.
2. **Unzip and open the folder** `intentlens/` in Kiro (File > Open Folder). Trust the workspace.
3. **Check steering is loaded.** Open the Kiro panel's steering section. You should see `product.md`, `tech.md`, `structure.md` as "always included".
4. **Open the spec.** In the Specs section you should see `intentlens` with requirements, design and tasks. If it does not appear, ask Kiro: "Index the existing spec in .kiro/specs/intentlens."
5. **Get your credentials ready** (do these in a browser, not in Kiro):
   - Neo4j AuraDB free instance (see `docs/SETUP_AURADB.md`). Save password at creation.
   - GitHub personal access token (public repo read).
   - An LLM key (Anthropic by default). Optional: Sarvam key.
6. **Create `.env`:** `cp .env.example .env` and fill it in yourself. **Never paste secrets into the Kiro chat.**
7. **Pick a work mode:** use *supervised* mode (review each change) for tasks 1 to 14, then autopilot is fine for UI and docs tasks.
8. **Git:** `git init && git add -A && git commit -m "scaffold"`. Commit after every task so you can roll back.

---

## Part 2: Kickoff prompt (paste once, in a Spec/Plan style chat)

```
You are the lead engineer for IntentLens (engine: IntentGraph), a hackathon project for hackFront India, PS 01 "Why The Code Is Like This", Neo4j track.

Read, in this order: .kiro/steering/product.md, tech.md, structure.md, then .kiro/specs/intentlens/requirements.md, design.md and tasks.md, then skim every file under backend/, scripts/, eval/ and frontend/src/.

Then do the following and STOP for my approval before changing any code:
1. Summarise the architecture in 10 lines.
2. List every gap, bug or risk you see between the spec and the existing code (be specific: file, function, issue).
3. Confirm the task order in tasks.md is dependency-correct; propose changes if not.
4. List what you need from me (credentials, decisions, sample data) before task 1.

Ground rules for the whole project:
- Work one task at a time, in the order of tasks.md. Do not start the next task until I say so.
- After each task: run `make test`, show me the result, update the task checkbox in tasks.md, and give me a one-paragraph summary plus the exact command I should run to verify.
- Never put secrets in code, logs or chat. Config only via backend/app/config.py.
- All Cypher is parameterised. The LLM never writes Cypher.
- Every LLM-derived claim must be traceable to a verbatim source quote or a graph fact.
- If something is uncertain or untested against live services, say so plainly instead of claiming it works.
```

Wait for Kiro's gap list. Fix the issues it finds as task 0 before continuing.

---

## Part 3: The task sequence (run in this order)

For each phase: paste the prompt, review the diff, run the **Verify** command, commit. Do not skip Verify.

### Phase A: Foundations (tasks 1 to 2)

**Prompt A**
```
Execute tasks 1 and 2 from .kiro/specs/intentlens/tasks.md.
Task 1: confirm the virtualenv and dependencies install cleanly and `make test` passes. Fix any import or dependency problems.
Task 2: review backend/app/graph/db.py and schema.cypher, make scripts/apply_schema.py robust (clear errors if credentials are wrong, idempotent), and add a `scripts/check_connection.py` that prints Neo4j version, index states, and whether the LLM key works (one tiny call).
Do not touch other modules. Show me the commands to run.
```
**Verify:** `make test`; `python -m scripts.check_connection`; `make schema` shows all indexes ONLINE.
**Done when:** AuraDB connected, constraints and 4 indexes exist, tests green.

### Phase B: Ingestion (tasks 3 to 5)

**Prompt B1 (git)**
```
Execute task 3. Review backend/app/ingestion/git_ingest.py. Requirements: resumable, rename detection preserved, diff capped, only files under SUBSYSTEM_PATHS, progress bar. Note that PyDriller's Repository(...).traverse_commits() walks the whole history; make this efficient for a large repo (for example by filtering with `filepath` per path or using `git log -- <paths>` to pre-select hashes, then fetching only those commits). Add a unit test with a tiny temporary git repo created in the test.
```
**Verify:** `make ingest` (git part); `wc -l data/cache/commits.jsonl`; inspect 3 records.

**Prompt B2 (GitHub)**
```
Execute task 4. Review backend/app/ingestion/github_ingest.py against the GitHub GraphQL schema. Fix field names if wrong, handle: pagination, secondary rate limits (retry-after), nodes with null authors, truncated comment lists (note when `first:N` limits are hit and add pagination for comments if needed), and PRs that touch the subsystem paths. Add a `--dry-run` flag that fetches 3 PRs and prints a summary. Add a unit test using a mocked httpx response.
```
**Verify:** `python -m backend.app.ingestion.github_ingest` on a small MAX_PRS (set MAX_PRS=10 in .env first), then inspect `data/cache/threads.jsonl`.

**Prompt B3 (documents)**
```
Execute task 5. Add backend/app/ingestion/doc_ingest.py: read in-repo design/README/CHANGELOG files and long explanatory comment blocks (for example the commented documentation above each key in redis.conf) in the configured paths, and emit Document evidence records to data/cache/documents.jsonl. Extend loader.py with load_documents (MERGE Document nodes with id=path#section, text, url) and wire it into scripts/build_graph.py. Add tests.
```
**Done when:** commits, threads and documents JSONL files exist and look sane. Commit.

### Phase C: Entities (tasks 6 to 8)

**Prompt C**
```
Execute tasks 6, 7 and 8 together, then stop.
6: harden extract_config_keys and parse_config_keys against real redis.conf formatting (commented defaults, quoted values, multi-value lines). Use real samples from data/repo/redis.conf in tests.
7: verify functions_from_hunks on real C diffs from data/cache/commits.jsonl; handle macros and multi-line signatures; add an optional tree-sitter path (behind a flag) only if hunk headers prove insufficient.
8: link commit and thread references (#123, Fixes #123) to PullRequest/Issue nodes; add REFERENCES edges in the loader.
Show precision on 20 random commits: print the extracted entities next to the commit subject so I can eyeball them.
```
**Verify:** `pytest`; eyeball the printed sample; fix what is wrong before moving on.

### Phase D: Load the evidence graph (tasks 9 to 10)

**Prompt D**
```
Execute tasks 9 and 10. Review backend/app/graph/loader.py and scripts/build_graph.py. Run `python -m scripts.build_graph --skip-mining` against AuraDB after confirming it is the intended instance. Then write scripts/graph_stats.py that prints node and relationship counts by label/type, and a handful of sanity Cypher checks (orphan commits, entities with no commits, duplicate persons). Re-run build_graph to prove idempotency (counts must not change).
```
**Verify:** `python -m scripts.graph_stats` before and after a second run: identical counts. Open Aura Explorer and look at one ConfigKey's neighbourhood.
**Done when:** evidence + entity layers are in the graph with no duplicates. Commit.

### Phase E: Decision mining (tasks 11 to 14)

**Prompt E1 (provider + prompts)**
```
Execute tasks 11 and 12. Finish backend/app/llm/provider.py (retry with backoff on rate limits, token and cost logging, the content-hash cache already exists: verify it works). Then create scripts/mine_sample.py that mines 10 hand-picked threads (I will give you ids) and prints each extracted decision with its verified quotes. Improve the SYSTEM prompt in decision_miner.py using what you see: add 2 few-shot examples (one with explicit rationale, one with no decision). Do not weaken the verbatim-quote rule.
```
**Verify:** run `python -m scripts.mine_sample pr:123 pr:456 ...`; read every output yourself. Reject decisions that are not real. Iterate the prompt until at least 7 of 10 are clearly correct.

**Prompt E2 (verification + agreement)**
```
Execute tasks 13 and 14. Make verify_decision robust to quote normalisation differences (smart quotes, markdown, whitespace). Make agreement_score use the same embedding model as retrieval. In loader.load_decisions confirm GOVERNS resolution works for config keys, functions and files, and that decisions with zero GOVERNS links are logged (they are unreachable by entity search). Then run `python -m scripts.build_graph --limit 50` and report: decisions found, decisions dropped by verification, decisions with no GOVERNS link, average agreement.
```
**Verify:** counts printed; spot-check 5 decisions in Aura Explorer.
**Then:** run the full `make build` (this spends LLM tokens; the cache protects re-runs). Commit.

### Phase F: Supersession (tasks 15 to 17)

**Prompt F**
```
Execute tasks 15, 16 and 17. 
15: test find_reverts and the structural linking Cypher against real revert commits in the graph.
16: review CLASSIFY_SYSTEM and pair selection. Currently only consecutive pairs per entity are classified; also classify any pair whose Decision embeddings have cosine similarity above 0.8 even if on different entities. Cap LLM calls and log the count.
17: run `make supersede`, then write scripts/show_supersession.py that prints every SUPERSEDES/REFINES/REVERTS edge with both titles, dates, reason and confidence. I will manually check at least 5 known cases.
```
**Verify:** read the printed edges. For each wrong one, tune the prompt or `MIN_CONF`. Record 5 confirmed supersession cases in `eval/gold_questions.json` (type "supersession").
**Done when:** at least 5 true supersession links are in the graph. Commit.

### Phase G: Question answering (tasks 18 to 23)

**Prompt G1 (retrieval)**
```
Execute tasks 18 to 20. Review backend/app/retrieval/graphrag.py end to end. Create scripts/ask_cli.py that takes a question and prints the full AnswerResponse JSON plus timing for each stage (link, fetch, generate). Write tests with a fake Neo4jDB and fake LLM covering: entity linking exact vs fulltext, vector fallback, replacement promotion, claim verification dropping uncited claims. Fix any Cypher errors against the live graph.
```
**Verify:** `python -m scripts.ask_cli "Why is repl-backlog-size 1mb?"` (use a real question from your graph).

**Prompt G2 (supersession-aware answers, confidence, refusal)**
```
Execute tasks 21 to 23. Verify the three behaviours with real questions and show me the outputs:
(a) a normal answered question with evidence and person to ask,
(b) a question whose best-matching decision is superseded: the answer must present the CURRENT decision and a banner explaining the replacement,
(c) an unanswerable question: must refuse with last changers and related discussions, and must never produce an invented rationale.
Add integration tests marked @pytest.mark.integration for these (skipped unless NEO4J_URI is set). Report p50 and p95 latency over 20 questions.
```
**Verify:** run the three cases yourself. If (c) ever answers, raise REFUSAL_THRESHOLD or tighten the vector-fallback cutoff (0.55) and add that question to the gold set.
**Done when:** answered, superseded and refused paths all behave. Commit.

### Phase H: API and UI (tasks 24 to 28)

**Prompt H1 (API)**
```
Execute task 24. Harden backend/app/main.py: request validation, timeout handling, structured error responses, request logging with latency, CORS restricted by an ALLOWED_ORIGINS env var, and a /ready endpoint that checks Neo4j and the LLM. Add API tests using FastAPI TestClient with the fake DB/LLM.
```
**Verify:** `make serve`, then `curl -X POST localhost:8000/ask -H 'Content-Type: application/json' -d '{"question":"..."}'`.

**Prompt H2 (UI)**
```
Execute tasks 25 to 28. In frontend/: run npm install, fix any NVL API or version issues (check the current @neo4j-nvl/react docs and adjust GraphView.jsx), and make the UI match src/styles.css. Required behaviours: answer card with clickable citations [E1], evidence chain rail, person to ask, status banner, confidence meter with reasons, distinct refusal state, graph view with status colours and click-to-inspect node details, loading and error states, keyboard accessible, usable at 375px width. Add a timeline strip for the entity's decisions in date order. Do not add new dependencies without telling me why.
```
**Verify:** `make serve` and `make ui`; test the three demo questions on desktop and a phone-width window.
**Done when:** the full demo flow works in the browser. Commit and tag `v0.1-demo`.

### Phase I: Evaluation (tasks 29 to 32)

**Prompt I**
```
Execute tasks 29 to 32. Help me fill eval/gold_questions.json: for each of 30 answerable questions I will provide (question, expected keywords, source URL); you validate the JSON schema, check no two questions are near-duplicates, and flag any whose expected keywords never appear in the graph text. Then run `make eval`, produce docs/EVALUATION_RESULTS.md, and add an LLM-judge option in eval/metrics.py for borderline keyword matches (report both numbers). Finally run a calibration check: mean confidence for correct vs incorrect answers, and propose adjustments to WEIGHTS and REFUSAL_THRESHOLD. Apply them only on the dev split; keep a held-out third untouched and report it separately.
```
**Verify:** open `docs/EVALUATION_RESULTS.md`. If IntentLens does not beat the baseline on supersession and refusal, that is the first thing to fix before polishing anything else.

### Phase J: Stretch, deploy, polish (tasks 33 to 36)

**Prompt J1 (Hinglish, optional, do after the core is stable)**
```
Execute task 33. Wire Sarvam into GraphRAG.normalize for lang=hi and lang=hinglish. First check Sarvam's current API docs for the correct endpoint, auth header and model name and fix backend/app/llm/provider.py if the placeholder is wrong. Keep code identifiers (like config keys) unchanged during translation. Add 5 Hinglish gold questions and report accuracy.
```

**Prompt J2 (deploy)**
```
Execute task 34. Create deployment config: backend Dockerfile and render.yaml (or Railway equivalent), frontend build for Vercel with an API base URL env var, and a deploy checklist in docs/DEPLOY.md. Make sure no secrets are committed and .env.example is complete. Run a smoke test script (scripts/smoke_test.py) against the deployed URL.
```

**Prompt J3 (demo hardening)**
```
Execute task 35. Create scripts/warm_demo.py that pre-asks the three demo questions so caches are hot, add a "demo mode" flag that pins those three questions' answers from cache if the LLM is slow, and verify docs/DEMO_SCRIPT.md matches what the app actually shows. List every way the live demo could fail and give me a mitigation for each.
```

**Prompt J4 (stretch)**
```
Execute task 36 only if tasks 1 to 35 are done. Build a minimal GitHub App webhook (FastAPI route) that replies to "/why <entity>" comments in a PR using /ask. Keep it behind a feature flag.
```

---

## Part 4: Recovery and quality prompts (use any time)

**Something is broken**
```
Stop adding features. Reproduce the failure, show me the exact error, find the root cause (not a workaround), fix it, add a regression test, and explain in three sentences what went wrong.
```

**Resume after a break**
```
Read .kiro/specs/intentlens/tasks.md and `git log --oneline -20`. Tell me which tasks are done, which is in progress, and what the next safe step is. Do not change code yet.
```

**Review before I commit**
```
Review the uncommitted diff as a strict reviewer: correctness, security (secrets, Cypher injection), error handling, missing tests, and deviations from the spec. List issues by severity. Do not fix anything until I choose.
```

**Check for hallucination risk**
```
Audit every place an LLM output is used. For each, show how it is validated before it reaches the graph or the user. List any path where an unverified LLM claim could be displayed, and fix those paths.
```

**Reduce cost**
```
Estimate token usage of build_graph and of /ask. Propose and implement caching, shorter prompts, and a cheaper model for classification steps without lowering gold-set accuracy. Show before/after numbers.
```

**Pitch prep**
```
Using docs/EVALUATION_RESULTS.md and the current app behaviour, fill docs/PITCH_OUTLINE.md with real numbers and real screenshots-to-capture. List three likely judge questions per slide with honest answers, including known limitations from README.md.
```

---

## Part 5: Suggested timeline (adapt to your phase dates)

| Block | Tasks | Output |
|---|---|---|
| Diagnose | 1 to 5, gold-set drafting | Repo chosen, ingestion working, 20 draft questions |
| Design, week 1 | 6 to 14 | Evidence + decision graph loaded |
| Design, week 2 | 15 to 24 | Supersession, Q&A, confidence, refusal, API |
| Deploy | 25 to 35 | UI, evaluation numbers, deployment, rehearsed demo |
| Stretch | 33, 36 | Hinglish, GitHub App |

## Part 6: Definition of done for the whole project
- [ ] `make test` green; integration tests green against AuraDB
- [ ] Graph loaded for one subsystem with at least 5 verified supersession links
- [ ] Demo flow works: answered, superseded, refused
- [ ] `docs/EVALUATION_RESULTS.md` shows IntentLens vs baseline with a held-out set
- [ ] Deployed URL works on a phone
- [ ] No secrets in git history
- [ ] Pitch deck and 3-minute demo rehearsed twice
