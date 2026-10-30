import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'
import AnswerCard from '../components/AnswerCard.jsx'
import { ANSWERED_FIXTURE, SUPERSEDED_FIXTURE, REFUSED_FIXTURE } from './fixtures.js'

// ── Answered state ────────────────────────────────────────────────────────────

describe('AnswerCard — answered state', () => {
  it('renders the decision title', () => {
    render(<AnswerCard res={ANSWERED_FIXTURE} />)
    expect(screen.getByText('Only show Redis logo if logging to stdout / TTY')).toBeInTheDocument()
  })

  it('renders the answer prose', () => {
    render(<AnswerCard res={ANSWERED_FIXTURE} />)
    expect(screen.getByText(/Redis only shows its logo/)).toBeInTheDocument()
  })

  it('renders citation chips for each evidence ref in the answer', () => {
    render(<AnswerCard res={ANSWERED_FIXTURE} />)
    const chips = screen.getAllByRole('button', { name: /Jump to evidence E/ })
    expect(chips.length).toBeGreaterThanOrEqual(2)
  })

  it('clicking a citation chip calls scrollIntoView on the evidence item', () => {
    const scrollMock = vi.fn()
    Element.prototype.scrollIntoView = scrollMock

    render(<AnswerCard res={ANSWERED_FIXTURE} />)
    const chip = screen.getByRole('button', { name: 'Jump to evidence E1' })
    fireEvent.click(chip)
    expect(scrollMock).toHaveBeenCalledOnce()
  })

  it('renders the evidence rail with both items', () => {
    render(<AnswerCard res={ANSWERED_FIXTURE} />)
    // Use getAllByText since E1/E2 appear in both the citation chip and rail ref
    expect(screen.getAllByText('E1').length).toBeGreaterThanOrEqual(2)
    expect(screen.getAllByText('E2').length).toBeGreaterThanOrEqual(1)
    // Verify the rail items themselves exist
    expect(document.getElementById('evidence-E1')).toBeInTheDocument()
    expect(document.getElementById('evidence-E2')).toBeInTheDocument()
  })

  it('renders evidence quote text', () => {
    render(<AnswerCard res={ANSWERED_FIXTURE} />)
    expect(screen.getByText('A new option always-show-logo was added.')).toBeInTheDocument()
  })

  it('renders the person-to-ask card', () => {
    render(<AnswerCard res={ANSWERED_FIXTURE} />)
    expect(screen.getByText('Salvatore Sanfilippo')).toBeInTheDocument()
    expect(screen.getByText('Made or approved this decision')).toBeInTheDocument()
  })

  it('renders confidence meter with label and score', () => {
    render(<AnswerCard res={ANSWERED_FIXTURE} />)
    const meter = screen.getByTestId('confidence-meter')
    expect(meter).toBeInTheDocument()
    expect(within(meter).getByText(/High/)).toBeInTheDocument()
    expect(within(meter).getByText(/80%/)).toBeInTheDocument()
  })

  it('renders five factor bars', () => {
    render(<AnswerCard res={ANSWERED_FIXTURE} />)
    const meter = screen.getByTestId('confidence-meter')
    expect(within(meter).getByText('Directness')).toBeInTheDocument()
    expect(within(meter).getByText('Corroboration')).toBeInTheDocument()
    expect(within(meter).getByText('Agreement')).toBeInTheDocument()
    expect(within(meter).getByText('Currency')).toBeInTheDocument()
    expect(within(meter).getByText('Distance')).toBeInTheDocument()
  })

  it('renders confidence reasons list', () => {
    render(<AnswerCard res={ANSWERED_FIXTURE} />)
    expect(screen.getByText('Rationale is stated explicitly in the source.')).toBeInTheDocument()
  })

  it('renders the decision card', () => {
    render(<AnswerCard res={ANSWERED_FIXTURE} />)
    expect(screen.getByTestId('decision-card')).toBeInTheDocument()
  })

  it('renders alternatives rejected in decision card', () => {
    render(<AnswerCard res={ANSWERED_FIXTURE} />)
    expect(screen.getByText(/Always show logo/)).toBeInTheDocument()
  })

  it('renders copy and share action buttons', () => {
    render(<AnswerCard res={ANSWERED_FIXTURE} />)
    expect(screen.getByText('Copy answer')).toBeInTheDocument()
    expect(screen.getByText('Share link')).toBeInTheDocument()
  })

  it('does NOT render superseded banner when superseded_notice is null', () => {
    render(<AnswerCard res={ANSWERED_FIXTURE} />)
    expect(screen.queryByTestId('superseded-banner')).not.toBeInTheDocument()
  })

  it('does NOT render history list when history is empty', () => {
    render(<AnswerCard res={ANSWERED_FIXTURE} />)
    expect(screen.queryByTestId('history-list')).not.toBeInTheDocument()
  })

  it('does NOT render refused view', () => {
    render(<AnswerCard res={ANSWERED_FIXTURE} />)
    expect(screen.queryByTestId('refused-view')).not.toBeInTheDocument()
  })
})

// ── Superseded state ──────────────────────────────────────────────────────────

describe('AnswerCard — superseded state', () => {
  it('renders the superseded banner', () => {
    render(<AnswerCard res={SUPERSEDED_FIXTURE} />)
    expect(screen.getByTestId('superseded-banner')).toBeInTheDocument()
  })

  it('banner contains the supersession notice text', () => {
    render(<AnswerCard res={SUPERSEDED_FIXTURE} />)
    const banner = screen.getByTestId('superseded-banner')
    expect(within(banner).getByText(/superseded/i)).toBeInTheDocument()
  })

  it('renders the replacement decision title in the banner', () => {
    render(<AnswerCard res={SUPERSEDED_FIXTURE} />)
    const banner = screen.getByTestId('superseded-banner')
    // The replacement title appears in a <strong> inside .ac-banner__replacement
    const replacement = within(banner).getByText('Delay BGSAVE only when AOF rewriting is active')
    expect(replacement.tagName).toBe('STRONG')
  })

  it('renders history list with the superseded older decision', () => {
    render(<AnswerCard res={SUPERSEDED_FIXTURE} />)
    const history = screen.getByTestId('history-list')
    expect(within(history).getByText('Avoid simultaneous RDB and AOF child process')).toBeInTheDocument()
  })

  it('older decision in history is struck through', () => {
    render(<AnswerCard res={SUPERSEDED_FIXTURE} />)
    const struck = screen.getByText('Avoid simultaneous RDB and AOF child process').closest('s')
    expect(struck).toBeInTheDocument()
  })

  it('current decision is shown with ACTIVE badge', () => {
    render(<AnswerCard res={SUPERSEDED_FIXTURE} />)
    const decision = screen.getByTestId('decision-card')
    expect(within(decision).getByText('active')).toBeInTheDocument()
  })

  it('confidence is shown at Medium level', () => {
    render(<AnswerCard res={SUPERSEDED_FIXTURE} />)
    expect(screen.getByText(/Medium/)).toBeInTheDocument()
  })

  it('renders the answered view (not refused)', () => {
    render(<AnswerCard res={SUPERSEDED_FIXTURE} />)
    expect(screen.getByTestId('answered-view')).toBeInTheDocument()
    expect(screen.queryByTestId('refused-view')).not.toBeInTheDocument()
  })
})

// ── Refused state ─────────────────────────────────────────────────────────────

describe('AnswerCard — refused state', () => {
  it('renders the refused view', () => {
    render(<AnswerCard res={REFUSED_FIXTURE} />)
    expect(screen.getByTestId('refused-view')).toBeInTheDocument()
  })

  it('shows the refusal heading', () => {
    render(<AnswerCard res={REFUSED_FIXTURE} />)
    expect(screen.getByText('No recorded rationale found')).toBeInTheDocument()
  })

  it('shows the refusal reason', () => {
    render(<AnswerCard res={REFUSED_FIXTURE} />)
    expect(screen.getByText(/No decision in the graph governs/)).toBeInTheDocument()
  })

  it('shows the will-not-guess note', () => {
    render(<AnswerCard res={REFUSED_FIXTURE} />)
    expect(screen.getByText(/IntentLens will not guess/)).toBeInTheDocument()
  })

  it('shows the person to ask', () => {
    render(<AnswerCard res={REFUSED_FIXTURE} />)
    expect(screen.getByText('Salvatore Sanfilippo')).toBeInTheDocument()
  })

  it('shows related history items', () => {
    render(<AnswerCard res={REFUSED_FIXTURE} />)
    expect(screen.getByText('Closest related history')).toBeInTheDocument()
    expect(screen.getByText(/Fix SDS string handling/)).toBeInTheDocument()
  })

  it('shows both last_change and discussion types', () => {
    render(<AnswerCard res={REFUSED_FIXTURE} />)
    expect(screen.getByText('Last change')).toBeInTheDocument()
    expect(screen.getByText('Discussion')).toBeInTheDocument()
  })

  it('does NOT render answered view or superseded banner', () => {
    render(<AnswerCard res={REFUSED_FIXTURE} />)
    expect(screen.queryByTestId('answered-view')).not.toBeInTheDocument()
    expect(screen.queryByTestId('superseded-banner')).not.toBeInTheDocument()
    expect(screen.queryByTestId('confidence-meter')).not.toBeInTheDocument()
  })

  it('does NOT render evidence rail or decision card', () => {
    render(<AnswerCard res={REFUSED_FIXTURE} />)
    expect(screen.queryByTestId('decision-card')).not.toBeInTheDocument()
    expect(screen.queryByTestId('history-list')).not.toBeInTheDocument()
  })
})

// ── HistoryList: mixed superseded + refined items ─────────────────────────────

import { MIXED_HISTORY_FIXTURE } from './fixtures.js'

describe('HistoryList — mixed superseded and refined items', () => {
  it('renders two history items', () => {
    render(<AnswerCard res={MIXED_HISTORY_FIXTURE} />)
    const historyList = screen.getByTestId('history-list')
    const items = within(historyList).getAllByRole('listitem')
    expect(items).toHaveLength(2)
  })

  it('strikes through the SUPERSEDED history item', () => {
    render(<AnswerCard res={MIXED_HISTORY_FIXTURE} />)
    const struckEl = screen.getByText('Always trim backlog on every replication write').closest('s')
    expect(struckEl).toBeInTheDocument()
  })

  it('does NOT strike through the ACTIVE (refined) history item', () => {
    render(<AnswerCard res={MIXED_HISTORY_FIXTURE} />)
    const titleEl = screen.getByText('Backlog trimming: avoid large node creation')
    expect(titleEl.closest('s')).toBeNull()
  })

  it('shows "Earlier decision, refined by the one above" label for ACTIVE item', () => {
    render(<AnswerCard res={MIXED_HISTORY_FIXTURE} />)
    expect(screen.getByText('Earlier decision, refined by the one above')).toBeInTheDocument()
  })

  it('does NOT show the refined label for SUPERSEDED item', () => {
    render(<AnswerCard res={MIXED_HISTORY_FIXTURE} />)
    // Only one refined label should exist (for the ACTIVE history item only)
    const labels = screen.getAllByText('Earlier decision, refined by the one above')
    expect(labels).toHaveLength(1)
  })

  it('shows superseded status badge for the SUPERSEDED item', () => {
    render(<AnswerCard res={MIXED_HISTORY_FIXTURE} />)
    // The superseded badge text
    const badges = screen.getAllByText('superseded')
    expect(badges.length).toBeGreaterThanOrEqual(1)
  })

  it('shows active status badge for the ACTIVE history item', () => {
    render(<AnswerCard res={MIXED_HISTORY_FIXTURE} />)
    // active badge appears in history
    const activeBadges = screen.getAllByText('active')
    // At least one active badge (could also appear in the main decision card)
    expect(activeBadges.length).toBeGreaterThanOrEqual(1)
  })
})
