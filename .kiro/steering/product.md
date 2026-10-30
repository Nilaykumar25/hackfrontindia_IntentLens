---
inclusion: always
---
# Product: IntentLens (engine: IntentGraph)

**Tagline:** Connect code to the decisions that shaped it.

IntentLens answers "why is the code like this?" for a real public repository. It ingests commits, pull requests, issues and in-repo docs, builds a Neo4j knowledge graph (IntentGraph) that links code entities to decisions, people and incidents, and answers questions with a cited chain of evidence.

## Non-negotiable behaviours
1. **Every answer carries evidence.** No sentence is shown unless it cites at least one evidence ID that exists in the graph.
2. **Supersession is honoured.** A decision with status SUPERSEDED or REVERSED is never presented as the current answer. It appears only as history, with a link to its replacement.
3. **Refusal is a feature.** If no decision governs the entity within MAX_GRAPH_HOPS, or confidence is below REFUSAL_THRESHOLD, the system refuses with a reason and shows the closest related discussions plus who last changed the entity.
4. **Confidence is computed from graph facts**, not from the LLM's self-assessment.
5. **The LLM never writes free-form Cypher against the graph.** Only parameterised templates in `backend/app/retrieval/cypher.py`.

## Users
New joiners, engineers about to refactor, tech leads auditing decisions, reviewers asking who to talk to.

## Hackathon context
hackFront India, theme AI and Developer Tools, PS 01 "Why The Code Is Like This", Neo4j track (Best Use of Neo4j). Optional Sarvam angle: Hindi/Hinglish questions.
