# Requirements Document: IntentLens

## Introduction
IntentLens is an Applied AI system that answers "why is the code like this?" for a public repository. It builds a Neo4j knowledge graph (IntentGraph) connecting code entities to decisions, evidence, people and incidents, then answers natural-language questions with cited evidence, supersession awareness and a confidence signal, and refuses when the graph holds no answer.

## Requirements

### Requirement 1: Repository ingestion
**User Story:** As a developer, I want the repository's history ingested, so that the reasoning behind the code is available for querying.

#### Acceptance Criteria
1. WHEN the ingest command runs THEN the system SHALL extract commits (hash, author, email, date, message, changed files, diff hunks) for the configured subsystem paths and cache them as JSONL.
2. WHEN a GitHub token is configured THEN the system SHALL fetch merged pull requests, review threads, comments, linked issues and changed files via the GraphQL API and cache them as JSONL.
3. IF the GitHub API rate limit is reached THEN the system SHALL wait until reset and resume without losing cached data.
4. WHEN ingestion is re-run THEN the system SHALL skip already-cached items.
5. WHEN design documents exist in the configured paths THEN the system SHALL ingest them as Document evidence.

### Requirement 2: Code entity extraction
**User Story:** As a developer, I want code entities identified, so that decisions can be attached to specific files, functions and configuration keys.

#### Acceptance Criteria
1. WHEN a commit changes a configuration file THEN the system SHALL identify the affected ConfigKey names and link the commit via MODIFIES.
2. WHEN a commit diff contains hunk headers THEN the system SHALL map hunks to Function entities and link the commit via MODIFIES.
3. WHEN a file is renamed THEN the system SHALL keep a single File identity using rename detection.
4. WHEN commit messages or PR bodies reference "#123" or "Fixes #123" THEN the system SHALL link them to the referenced PullRequest or Issue.

### Requirement 3: Decision mining
**User Story:** As a developer, I want decisions extracted from discussions, so that answers cite a decision rather than raw text.

#### Acceptance Criteria
1. WHEN a PR, issue or substantial commit thread is processed THEN the system SHALL extract zero or more Decisions with title, summary, rationale, alternatives rejected, decision-makers, date and source quotes.
2. WHEN a Decision is extracted THEN every quote SHALL be verified to exist verbatim (whitespace-normalised) in the source text, and decisions without a verifiable quote SHALL be discarded.
3. WHEN a rationale is inferred rather than stated THEN the Decision SHALL be flagged explicit_rationale=false.
4. WHEN two independent extraction passes are run THEN the system SHALL store an agreement score between 0 and 1.
5. WHEN a Decision is stored THEN it SHALL have an embedding for vector retrieval and GOVERNS links to the entities it concerns.

### Requirement 4: Knowledge graph
**User Story:** As a maintainer, I want a well-typed graph, so that traversal queries are fast and correct.

#### Acceptance Criteria
1. WHEN the schema command runs THEN the system SHALL create uniqueness constraints, a full-text index over entity names and decision text, and a vector index over Decision embeddings.
2. WHEN data is loaded THEN the system SHALL use idempotent MERGE operations so re-runs do not create duplicates.
3. WHEN a node is evidence THEN it SHALL carry a stable id, url, timestamp and text.

### Requirement 5: Supersession detection
**User Story:** As a developer, I do not want to be told a dead decision is current, so that I do not act on outdated reasoning.

#### Acceptance Criteria
1. WHEN a commit reverts another commit THEN the system SHALL link the Decisions evidenced by them with REVERTS and mark the older Decision REVERSED.
2. WHEN two Decisions govern the same entity THEN the system SHALL classify the newer relative to the older as reinforces, refines, contradicts or unrelated, storing a reason and confidence.
3. WHEN the classification is contradicts with confidence at or above 0.6 THEN the older Decision SHALL be marked SUPERSEDED with a SUPERSEDES edge from the newer.
4. IF the classification confidence is below 0.6 THEN the older Decision SHALL be marked UNCERTAIN and the answer SHALL say "possibly superseded".
5. Superseded Decisions SHALL never be deleted.

### Requirement 6: Evidence-backed question answering
**User Story:** As a developer, I want to ask "why" and get the decision, the discussion, the person to ask and the date.

#### Acceptance Criteria
1. WHEN a question is submitted THEN the system SHALL link it to graph entities using full-text and vector search.
2. WHEN entities are linked THEN the system SHALL retrieve governing Decisions and their evidence using parameterised Cypher templates only.
3. WHEN an answer is generated THEN each claim SHALL cite evidence IDs and any claim without a valid citation SHALL be removed.
4. WHEN the governing Decision has been superseded THEN the answer SHALL state this, with the date and the replacing Decision.
5. WHEN an answer is returned THEN it SHALL include the person to ask, the decision date and an evidence timeline.

### Requirement 7: Confidence and refusal
**User Story:** As a developer, I want to know how much to trust an answer, and I want the system to say "I don't know" instead of inventing one.

#### Acceptance Criteria
1. WHEN an answer is produced THEN the system SHALL compute a confidence score from evidence directness, corroboration, extraction agreement, code currency and graph distance, and return the factors.
2. WHEN the score maps below REFUSAL_THRESHOLD OR no Decision lies within MAX_GRAPH_HOPS THEN the system SHALL refuse, state why, and return the last changers and closest related discussions.
3. The confidence label SHALL be High, Medium, Low or No answer.

### Requirement 8: User interface
**User Story:** As a developer, I want a clear interface to ask questions and inspect evidence.

#### Acceptance Criteria
1. WHEN an answer is returned THEN the UI SHALL show answer, decision, evidence chain, person to ask, status banner and confidence with reasons.
2. WHEN a decision is superseded THEN the UI SHALL show a warning banner linking to the replacement.
3. WHEN the system refuses THEN the UI SHALL show a distinct refusal state with the closest related discussions.
4. WHEN the user opens the graph view THEN the UI SHALL render the decision neighbourhood using Neo4j NVL with decisions coloured by status.
5. The UI SHALL be usable at mobile widths and keyboard accessible.

### Requirement 9: Evaluation
**User Story:** As a team, we want measured results against a baseline, so that our claims are credible.

#### Acceptance Criteria
1. WHEN the eval command runs THEN the system SHALL evaluate IntentLens and a vector-only RAG baseline on the same gold set (answerable, unanswerable, supersession cases).
2. WHEN evaluation completes THEN the system SHALL report answer accuracy, citation precision, supersession recall/precision, refusal correctness, calibration and latency as a Markdown table.

### Requirement 10: Multilingual input (stretch)
1. WHERE a Hindi or Hinglish question is submitted THEN the system SHALL normalise it to English via the configured LLM before entity linking and answer in the user's language.

### Requirement 11: Non-functional
1. The /ask endpoint SHOULD respond within 12 seconds for 95 percent of gold-set questions.
2. Secrets SHALL only be read from environment variables.
3. The pipeline SHALL be resumable and idempotent.
