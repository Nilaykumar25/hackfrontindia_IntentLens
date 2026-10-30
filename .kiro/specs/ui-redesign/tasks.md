# Implementation Plan: IntentLens UI Redesign

Work stage by stage. After each stage: run `npm run build`, list files changed, describe what to look at, and wait for "go".

---

## Stage 0: Backend additions
Add `/stats`, `/entities/search`, `/eval/results` endpoints to `backend/app/main.py`. Add tests. No frontend changes.

- [ ] Add `GET /stats` endpoint (commits, decisions, superseded, persons, entities)
- [ ] Add `GET /entities/search?q=` endpoint (fulltext, top 8)
- [ ] Add `GET /eval/results` endpoint (parse EVALUATION_RESULTS.md)
- [ ] Add backend tests for all three new endpoints
- [ ] Verify `make test` passes

---

## Stage 1: Design tokens, reset, routing scaffold
Install `react-router-dom`. Create `tokens.css`, `reset.css`. Wire up the router with lazy-loaded page stubs. Update `main.jsx`, `App.jsx`, `index.html`. Update `api.js` with new calls.

- [ ] `npm install react-router-dom`
- [ ] Create `src/tokens.css` (all CSS custom properties from design.md)
- [ ] Create `src/reset.css` (base reset + body font, bg, colour)
- [ ] Update `src/main.jsx` to wrap in `<BrowserRouter>`
- [ ] Update `src/App.jsx` with lazy routes (Landing, Ask, Explore, How, Results, About)
- [ ] Create stub `src/pages/Landing.jsx`, `Ask.jsx`, `Explore.jsx`, `How.jsx`, `Results.jsx`, `About.jsx`
- [ ] Create `src/components/Nav.jsx` (logo, links, theme toggle)
- [ ] Create `src/components/Footer.jsx`
- [ ] Update `src/api.js` with `getStats()`, `searchEntities(q)`, `getEvalResults()`
- [ ] Update `index.html` with new font links (Fraunces, Outfit, JetBrains Mono)
- [ ] Run `npm run build` and confirm no errors

**Stop and wait for "go".**

---

## Stage 2: Design system components
Build the shared components that every page uses: StatusBadge, Skeleton, ThreadIllustration (SVG animation), StatsStrip.

- [ ] Create `src/components/StatusBadge.jsx`
- [ ] Create `src/components/Skeleton.jsx`
- [ ] Create `src/components/ThreadIllustration.jsx` (animated SVG, aria-hidden, sample label)
- [ ] Create `src/components/StatsStrip.jsx` (calls /stats, quiet empty state)
- [ ] Run `npm run build`

**Stop and wait for "go".**

---

## Stage 3: Landing page
Build all eight sections of `/`. Uses ThreadIllustration, StatsStrip, real copy.

- [ ] Hero section (tagline, CTAs, ThreadIllustration)
- [ ] Problem section (4 failure modes)
- [ ] Capabilities section (3 features with UI fragments)
- [ ] Pipeline SVG diagram
- [ ] Stats strip
- [ ] Built-on strip
- [ ] India section
- [ ] Final CTA + Footer
- [ ] Mobile layout (375px)
- [ ] Run `npm run build`

**Stop and wait for "go".**

---

## Stage 4: Ask workspace (`/ask`)
Rebuild the main app page with the two-pane layout, all answer states, evidence rail, confidence meter.

- [ ] `QuestionComposer` component (input, lang select, suggestions, recent in memory)
- [ ] `AnswerView` component shell
- [ ] Empty state (ThreadIllustration + 3 starter questions)
- [ ] Loading skeleton with stage text
- [ ] `EvidenceRail.jsx` component
- [ ] `ConfidenceMeter.jsx` component (five-factor bars)
- [ ] `DecisionCard` + `PersonCard` inline components
- [ ] Answered state (all sub-components wired)
- [ ] [E1] click → scroll-to highlight
- [ ] Superseded banner state
- [ ] Refused state (last changers + discussions)
- [ ] Error state (retry button)
- [ ] Copy-answer and share-link buttons
- [ ] Mobile: graph preview collapses
- [ ] Run `npm run build`

**Stop and wait for "go".**

---

## Stage 5: Explore, How, Results, About pages
Four remaining pages.

### Explore (`/explore`)
- [ ] Entity search with autocomplete (GET /entities/search)
- [ ] Lazy-loaded GraphView
- [ ] Side panel for node details
- [ ] Filter chips
- [ ] Timeline strip

### How (`/how`)
- [ ] Pipeline steps
- [ ] Graph schema SVG
- [ ] Supersession algorithm worked example
- [ ] Confidence formula

### Results (`/results`)
- [ ] Fetch GET /eval/results
- [ ] Comparison table + bar visuals
- [ ] Honest 404 empty state

### About (`/about`)
- [ ] Project summary, hackathon context
- [ ] Tech stack
- [ ] Known limitations
- [ ] Team placeholders (clearly labelled)

- [ ] Run `npm run build`

**Stop and wait for "go".**

---

## Stage 6: Polish, accessibility audit, final build
- [ ] Verify WCAG AA contrast in both themes (dev tools)
- [ ] Keyboard navigation test (Tab through all pages)
- [ ] 375px layout test
- [ ] `prefers-reduced-motion` test
- [ ] `prefers-color-scheme: light` test
- [ ] Focus rings visible on all interactive elements
- [ ] All SVGs have aria-label or title
- [ ] Run `npm run build`
- [ ] Run `make test` (backend unchanged)
- [ ] Tag `v0.1-demo`

**Done.**
