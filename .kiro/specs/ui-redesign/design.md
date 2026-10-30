# Design Document: IntentLens UI Redesign

## Overview
The redesign replaces the single-column prototype with a complete product: a landing page that communicates the core idea, a two-pane workspace for asking questions, a graph explorer, and supporting pages. Every screen expresses "the evidence trail" concept — answers are chains, not guesses.

## New dependencies required
- `react-router-dom@^6` — client-side routing. Required for the multi-page IA.
  No other new dependencies. The graph view keeps `@neo4j-nvl/react`. Fonts via Google Fonts link tag.

## File structure (frontend/src)
```
src/
  main.jsx                   Entry point; wraps App in BrowserRouter
  App.jsx                    Route declarations (lazy-loaded pages)
  api.js                     Existing; add stats, search, evalResults calls
  tokens.css                 CSS custom properties (design tokens)
  reset.css                  CSS reset + base styles
  pages/
    Landing.jsx              /
    Ask.jsx                  /ask
    Explore.jsx              /explore
    How.jsx                  /how
    Results.jsx              /results
    About.jsx                /about
  components/
    Nav.jsx                  Top navigation + theme toggle
    Footer.jsx               Footer
    AnswerCard.jsx           Answer view (all states)
    GraphView.jsx            NVL wrapper (lazy)
    EvidenceRail.jsx         Vertical evidence chain
    ConfidenceMeter.jsx      Five-factor bar chart
    ThreadIllustration.jsx   SVG evidence-trail animation
    StatsStrip.jsx           Live stats from /stats
    Skeleton.jsx             Loading skeleton blocks
    StatusBadge.jsx          ACTIVE / SUPERSEDED / etc.
```

## Design tokens (tokens.css)
Implements all tokens from .kiro/steering/design.md. Both dark (default) and light themes via `@media (prefers-color-scheme: light)`. Theme toggle overrides via `data-theme="light"` on `<html>`.

## Landing page layout
```
[Nav]
[Hero — 2col: copy left, ThreadIllustration right]
[Problem — 4-col grid of failure modes]
[Capabilities — 3 feature cards with UI fragments]
[Pipeline — inline SVG]
[Stats strip — live counts]
[Built-on strip]
[India section]
[CTA]
[Footer]
```

## Ask page layout
```
[Nav]
[2-pane: 380px left | flex-1 right]
  Left: QuestionComposer (input, lang select, suggestions, recent)
  Right: AnswerView (empty | loading | answered | superseded | refused | error)
    answered: Answer prose → DecisionCard → PersonCard → EvidenceRail → HistoryList → ConfidenceMeter → GraphPreview
[Mobile <768px: stacked, GraphPreview collapses]
```

## Evidence-trail SVG animation
The signature motif is an SVG with:
- Nodes: circles with labels (ConfigKey, Decision, Person, Commit)
- Edges: `stroke-dasharray` + `stroke-dashoffset` animated to 0 over 800ms, staggered by 120ms per edge
- On the landing hero: 6-node sample trail, pre-labelled "Sample answer"
- In the ask page empty state: smaller version
- Respects `prefers-reduced-motion`

## Status colours (applied consistently)
- ACTIVE: `--active` green pill badge
- SUPERSEDED: `--superseded` orange pill badge  
- REVERSED: `--reversed` red pill badge
- UNCERTAIN: `--uncertain` yellow pill badge
- refused: `--refused` slate left-border card

## Evidence rail
Vertical timeline with left border. Each item:
- Icon (Commit / PR / Issue / Document) in a coloured circle
- Monospace ID + date + author
- Snippet text or verbatim quote
- [E1] chip on hover scrolls to and highlights this item

## Confidence meter
Five horizontal bars, one per factor (directness, corroboration, agreement, currency, distance). Each bar shows the factor name, its contribution, and fills proportionally. Below: label (High / Medium / Low / No answer) with amber colouration for High.

## Backend endpoints (new)

### GET /stats
Returns:
```json
{
  "commits": 1372,
  "decisions": 64,
  "superseded": 5,
  "persons": 249,
  "entities": 467
}
```

### GET /entities/search?q=
Returns:
```json
[
  {"id": "config:repl-backlog-size", "name": "repl-backlog-size", "type": "ConfigKey"},
  ...
]
```
Top 8 by full-text match.

### GET /eval/results
Parses `docs/EVALUATION_RESULTS.md`, returns:
```json
{
  "dev": {"answer_accuracy": 0.75, ...},
  "held_out": {...},
  "baseline": {...}
}
```
404 if file missing.

## Routing and code splitting
```jsx
// App.jsx
const Landing = lazy(() => import('./pages/Landing'))
const Ask     = lazy(() => import('./pages/Ask'))
const Explore = lazy(() => import('./pages/Explore'))
const How     = lazy(() => import('./pages/How'))
const Results = lazy(() => import('./pages/Results'))
const About   = lazy(() => import('./pages/About'))
```

GraphView is additionally wrapped in a second `lazy()` inside Explore.jsx.

## Accessibility
- All interactive elements have visible focus rings
- Skip-to-main link at top of Nav
- Semantic HTML: `<header>`, `<nav>`, `<main>`, `<aside>`, `<footer>`
- SVG diagrams have `<title>` and `aria-label`
- The ThreadIllustration has `aria-hidden="true"` and a visible text caption
- EvidenceRail items have `aria-label` combining ref + type + date
