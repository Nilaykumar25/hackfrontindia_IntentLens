# Requirements: IntentLens UI Redesign

## Overview
Full redesign of the IntentLens frontend. The backend is complete. This spec covers the new information architecture, design system, all pages, backend additions, and accessibility requirements.

---

## REQ-01: Design system and theme

**R01.1** WHEN the user's OS is set to dark mode THEN the UI SHALL display the ink-dark theme by default.

**R01.2** WHEN the user's OS is set to light mode THEN the UI SHALL display the light theme by default.

**R01.3** WHERE a theme toggle is present THEN it SHALL override the OS preference and persist to localStorage.

**R01.4** WHEN the UI renders THEN ALL text-and-background pairs SHALL meet WCAG AA contrast (4.5:1 for normal, 3:1 for large text) in both themes.

**R01.5** WHEN the user activates `prefers-reduced-motion: reduce` THEN ALL animations and transitions SHALL be disabled.

**R01.6** WHEN the UI renders THEN it SHALL use Fraunces (display), Outfit (UI sans), and JetBrains Mono (monospace) only. No Inter, Roboto, Arial, or system-only stacks SHALL be used as the primary type stack.

**R01.7** WHERE focus is placed on any interactive element THEN a visible focus ring SHALL appear (3px solid amber, 2px offset).

---

## REQ-02: Information architecture and routing

**R02.1** WHEN the user navigates to `/` THEN the landing page SHALL render.

**R02.2** WHEN the user navigates to `/ask` THEN the question workspace SHALL render.

**R02.3** WHEN the user navigates to `/explore` THEN the graph explorer SHALL render.

**R02.4** WHEN the user navigates to `/how` THEN the how-it-works page SHALL render.

**R02.5** WHEN the user navigates to `/results` THEN the evaluation results page SHALL render.

**R02.6** WHEN the user navigates to `/about` THEN the about page SHALL render.

**R02.7** WHEN the application loads THEN routes SHALL be code-split at the route level so the landing page does NOT load the graph view bundle.

---

## REQ-03: Landing page (`/`)

**R03.1** WHEN the landing page renders THEN it SHALL show a hero section with the tagline "Connect code to the decisions that shaped it." a one-sentence description, a primary CTA to `/ask`, and a secondary CTA to `/how`.

**R03.2** WHEN the hero renders THEN it SHALL show an animated evidence-trail illustration beside the text using static sample data CLEARLY labelled "Sample answer".

**R03.3** WHEN the landing page renders THEN it SHALL show a problem section with the title "When the senior engineer leaves, the reasoning leaves too." listing four failure modes.

**R03.4** WHEN the landing page renders THEN it SHALL show a capabilities section with three features: Evidence on every answer, Supersession awareness, Honest refusal; each with a small illustrative UI fragment.

**R03.5** WHEN the landing page renders THEN it SHALL show an inline SVG pipeline diagram: Ingest → Graph → Mine decisions → Detect supersession → Answer with confidence.

**R03.6** WHEN the landing page calls `GET /stats` and the API responds THEN the landing page SHALL display real counts for commits, decisions, superseded decisions, and people.

**R03.7** WHEN `GET /stats` fails or returns no data THEN the stats strip SHALL show a quiet empty state with no fake numbers.

**R03.8** WHEN the landing page renders THEN it SHALL show a "Built on" strip listing Neo4j AuraDB, GraphRAG, Sarvam, FastAPI, and React using text or simple marks only. No external image hosts.

**R03.9** WHEN the landing page renders THEN it SHALL show a section about why this matters for Indian engineering teams, using factual and modest language with no invented claims.

**R03.10** WHEN the landing page renders THEN it SHALL show a final CTA section and a footer with links to `/about` and the public repository.

---

## REQ-04: Ask workspace (`/ask`)

**R04.1** WHEN `/ask` renders THEN it SHALL use a two-pane layout with the question composer on the left and the answer view on the right.

**R04.2** WHEN the answer view is in the empty state THEN it SHALL show the evidence-trail illustration and three starter questions.

**R04.3** WHEN the backend is processing a question THEN the answer view SHALL show a skeleton that mimics the answer card structure with stage text "Linking entities", "Traversing graph", "Verifying citations" in sequence.

**R04.4** WHEN an answer is returned with `status: answered` THEN the answer view SHALL show: the answer prose with clickable [E1] citation chips, a decision card (title, date, status badge), a person-to-ask card, a vertical evidence rail with icons and monospace IDs, earlier decisions struck through, and a confidence meter with five-factor bars and plain-language reasons.

**R04.5** WHEN an [E1] citation chip is clicked THEN the page SHALL scroll to and highlight the matching evidence item in the rail.

**R04.6** WHEN an answer is returned with `status: answered` AND the decision was superseded THEN the answer view SHALL show a prominent banner linking to the replacing decision.

**R04.7** WHEN an answer is returned with `status: refused` THEN the answer view SHALL show a distinct calm state with the refusal reason, last changers, and closest related discussions. It SHALL NOT show an empty article or any invented content.

**R04.8** WHEN a network error occurs THEN the answer view SHALL show an error state with a retry button.

**R04.9** WHEN `/ask` renders on a screen narrower than 768px THEN the graph preview SHALL collapse beneath the answer card.

**R04.10** WHEN the user submits a question THEN recent questions SHALL be stored in memory (not localStorage) and shown as suggestions.

**R04.11** WHEN an answer is shown THEN copy-answer and share-link buttons SHALL be present.

---

## REQ-05: Graph explorer (`/explore`)

**R05.1** WHEN `/explore` renders THEN it SHALL show a search box with entity autocomplete powered by `GET /entities/search?q=`.

**R05.2** WHEN an entity is selected THEN the full-height graph SHALL render using Neo4j NVL with status colours.

**R05.3** WHEN a node is clicked THEN a side panel SHALL open with the node's details.

**R05.4** WHEN the graph renders THEN filter chips SHALL allow filtering by node type and status.

**R05.5** WHEN an entity is selected THEN a timeline strip of that entity's decisions in date order SHALL be shown.

**R05.6** WHEN the user navigates to `/explore` THEN the NVL graph SHALL be lazy-loaded so it does not affect initial bundle size.

---

## REQ-06: How it works (`/how`)

**R06.1** WHEN `/how` renders THEN it SHALL show a step-by-step explanation of the pipeline.

**R06.2** WHEN `/how` renders THEN it SHALL show the graph schema as an inline SVG diagram.

**R06.3** WHEN `/how` renders THEN it SHALL show the supersession algorithm (three signals) with a worked example.

**R06.4** WHEN `/how` renders THEN it SHALL show the confidence formula with all five weights displayed.

---

## REQ-07: Results (`/results`)

**R07.1** WHEN `/results` renders THEN it SHALL call `GET /eval/results`.

**R07.2** WHEN `GET /eval/results` responds with data THEN the page SHALL show IntentLens vs vector-RAG baseline as a comparison table plus bar visuals.

**R07.3** WHEN `GET /eval/results` returns 404 THEN the page SHALL show an honest empty state explaining how to run `make eval`. No placeholder numbers SHALL be shown.

---

## REQ-08: About (`/about`)

**R08.1** WHEN `/about` renders THEN it SHALL show the project summary, hackathon context (hackFront India, PS 01, Neo4j track), tech stack, and known limitations.

**R08.2** WHERE team placeholders are shown THEN they SHALL be CLEARLY labelled as placeholders.

---

## REQ-09: Backend additions

**R09.1** WHEN `GET /stats` is called THEN the API SHALL return counts of commits, decisions, superseded/reversed decisions, persons, and entities as JSON.

**R09.2** WHEN `GET /entities/search?q=` is called THEN the API SHALL return the top 8 entities by full-text match with id, name, and type.

**R09.3** WHEN `GET /eval/results` is called and `docs/EVALUATION_RESULTS.md` exists THEN the API SHALL parse the Markdown table and return structured JSON.

**R09.4** WHEN `GET /eval/results` is called and `docs/EVALUATION_RESULTS.md` does not exist THEN the API SHALL return 404.

**R09.5** The shape of `POST /ask` and `GET /entity/graph` SHALL NOT be changed.

---

## REQ-10: Cross-cutting constraints

**R10.1** The UI SHALL be usable at 375px width.

**R10.2** Touch targets SHALL be a minimum of 44×44px.

**R10.3** All SVG diagrams SHALL have `aria-label` or `<title>` elements.

**R10.4** Every claim shown to users SHALL be backed by real data or clearly labelled as "Sample".

**R10.5** No secrets SHALL appear in frontend code. No external image hosts SHALL be used. Fonts via Google Fonts are permitted.

**R10.6** The existing `frontend/src/api.js` contract SHALL be preserved.
