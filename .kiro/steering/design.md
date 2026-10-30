---
inclusion: always
---
# Design System: IntentLens

## Skill applied
`frontend-design` skill (from `C:\Users\NILAY\.agents\skills\frontend-design\SKILL.md`) was read and the following guidance is applied:
- The amber accent is a *deliberate choice for this brief* — evidence is something found, illuminated — not the default terracotta. NOT the generic cream/terracotta palette.
- One memorable element per page (evidence-thread SVG hero); everything else is quiet and disciplined.
- Motion used once per page (page-load) and once for the signature interaction (thread drawing). NO hover-on-every-card transitions.
- NO ALL-CAPS labels, NO tracked-out eyebrows above headings, NO middle-dot meta strings.
- Copy: sentence case, active voice, plain verbs. CTA says exactly what happens: "Ask the codebase".
- Type: Fraunces (display, slightly technical feel for surfacing old decisions) + Outfit (clean UI sans, not Inter/Roboto). A deliberate pairing for *this* brief.
- Layout: NOT the rounded-card SaaS kit. Cards only where content needs grouping. Avoid card-on-card nesting.

## Concept
"The evidence trail." Every screen reinforces that answers are traced back through a chain: code entity → decision → discussion → person → date. The signature motif is thin connecting threads drawn between nodes (SVG stroke animation) on the landing hero, in the evidence chain, and in the graph view.

## Colour tokens

### Dark theme (default — `prefers-color-scheme: dark`)
| Token | Value | Usage |
|-------|-------|-------|
| `--bg` | `#0d1117` | Page background |
| `--surface` | `#161b22` | Cards, panels |
| `--surface-2` | `#1c232c` | Raised surfaces, hover |
| `--ink` | `#e6edf3` | Primary text |
| `--muted` | `#8b949e` | Secondary text |
| `--line` | `#30363d` | Borders, dividers |
| `--accent` | `#e8a838` | Lens amber — primary actions, evidence highlights |
| `--accent-soft` | `#3a2f1a` | Amber tint backgrounds |
| `--active` | `#3fb950` | Decision status: ACTIVE |
| `--superseded` | `#d29922` | Decision status: SUPERSEDED |
| `--reversed` | `#f85149` | Decision status: REVERSED |
| `--uncertain` | `#d2a838` | Decision status: UNCERTAIN |
| `--refused` | `#6e7681` | Refusal state |
| `--entity` | `#58a6ff` | Code entity nodes |

### Light theme (`prefers-color-scheme: light`)
| Token | Value |
|-------|-------|
| `--bg` | `#f6f8fa` |
| `--surface` | `#ffffff` |
| `--surface-2` | `#eef1f4` |
| `--ink` | `#1f2328` |
| `--muted` | `#59636e` |
| `--line` | `#d1d9e0` |
| `--accent` | `#b8821f` |
| `--accent-soft` | `#fff5e0` |
| `--active` | `#1a7f37` |
| `--superseded` | `#9a6700` |
| `--reversed` | `#cf222e` |
| `--uncertain` | `#9a8400` |
| `--refused` | `#57606a` |
| `--entity` | `#0969da` |

All text-and-background combinations meet WCAG AA (4.5:1 for normal text, 3:1 for large text) in both themes.

## Typography

| Role | Font | Weights | Google Fonts |
|------|------|---------|-------------|
| Display | Fraunces | 400, 500, 600 | Yes |
| UI sans | Outfit | 300, 400, 500, 600 | Yes |
| Mono | JetBrains Mono | 400, 500 | Yes |

No Inter, Roboto, Arial, or system-only stacks.

### Type scale
| Name | Size | Line height | Weight | Family | Usage |
|------|------|-------------|--------|--------|-------|
| `--text-hero` | clamp(2.5rem, 5vw, 4rem) | 1.05 | 500 | Fraunces | Landing hero |
| `--text-h1` | 2rem | 1.15 | 500 | Fraunces | Page titles |
| `--text-h2` | 1.5rem | 1.25 | 500 | Fraunces | Section titles |
| `--text-h3` | 1.125rem | 1.35 | 500 | Outfit | Card titles |
| `--text-body` | 1rem | 1.6 | 400 | Outfit | Body text |
| `--text-read` | 1.125rem | 1.7 | 400 | Fraunces | Answer prose |
| `--text-sm` | 0.875rem | 1.45 | 400 | Outfit | Captions, meta |
| `--text-xs` | 0.75rem | 1.4 | 500 | Outfit | Labels, badges |
| `--text-mono` | 0.8125rem | 1.5 | 400 | JetBrains Mono | IDs, hashes, config keys |

## Spacing scale
Based on a 4px grid: `--space-1` (4px), `--space-2` (8px), `--space-3` (12px), `--space-4` (16px), `--space-5` (20px), `--space-6` (24px), `--space-8` (32px), `--space-10` (40px), `--space-12` (48px), `--space-16` (64px), `--space-20` (80px).

## Radius
`--radius-sm: 4px`, `--radius-md: 8px`, `--radius-lg: 12px`, `--radius-full: 9999px`.

## Motion

| Token | Duration | Easing | Usage |
|-------|---------|--------|-------|
| `--motion-fast` | 150ms | `ease-out` | Hover, focus, small state changes |
| `--motion-base` | 300ms | `cubic-bezier(0.2, 0, 0, 1)` | Page reveals, card transitions |
| `--motion-slow` | 600ms | `cubic-bezier(0.2, 0, 0, 1)` | SVG thread drawing animation |

### Rules
- Staged page-load reveals: elements fade in + translateY(8px) with 60ms stagger.
- Evidence threads: SVG `stroke-dashoffset` animation from full to 0 over 800ms.
- Hover and focus states on every interactive element.
- `prefers-reduced-motion: reduce` disables all animations and transitions.

## Tone of voice
- Plain, confident, specific.
- No hype words ("amazing", "revolutionary", "game-changing").
- No invented statistics or fake testimonials.
- Sample data is always labelled "Sample".
- Refusal is described calmly: "The graph does not contain a decision that explains this."

## Accessibility
- WCAG AA contrast in both themes.
- Visible focus rings (3px solid `--accent`, offset 2px).
- Semantic landmarks: `<header>`, `<nav>`, `<main>`, `<aside>`, `<footer>`.
- `aria-label` on all icon-only buttons and SVG diagrams.
- Keyboard navigable: Tab order follows visual order; Enter activates.
- Touch targets minimum 44×44px.
- Usable at 375px width.
