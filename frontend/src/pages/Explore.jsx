import { lazy, Suspense, useState, useEffect, useRef, useCallback } from 'react'
import { searchEntities } from '../api.js'
import Badge from '../components/Badge.jsx'
import Skeleton from '../components/Skeleton.jsx'
import Button from '../components/Button.jsx'
import './Explore.css'

/* GraphView is lazy-loaded so the NVL bundle doesn't load until needed */
const GraphView = lazy(() => import('../components/GraphView.jsx'))

const NODE_TYPES   = ['Decision', 'Entity', 'ConfigKey', 'Function', 'File', 'Commit', 'Person', 'Document']
const STATUS_TYPES = ['ACTIVE', 'SUPERSEDED', 'REVERSED', 'UNCERTAIN']
const MAX_NODES    = 150

/* ── Entity autocomplete search ─────────────────────────── */
function EntitySearch({ onSelect }) {
  const [q, setQ]           = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [open, setOpen]       = useState(false)
  const debounce = useRef(null)

  useEffect(() => {
    clearTimeout(debounce.current)
    if (!q.trim()) { setResults([]); setOpen(false); return }
    debounce.current = setTimeout(async () => {
      setLoading(true)
      const data = await searchEntities(q).catch(() => [])
      setResults(data)
      setOpen(data.length > 0)
      setLoading(false)
    }, 280)
  }, [q])

  const pick = useCallback((entity) => {
    setQ(entity.name)
    setOpen(false)
    onSelect(entity)
  }, [onSelect])

  return (
    <div className="explore-search" role="search" aria-label="Search entities">
      <div className="explore-search__input-wrap">
        <input
          className="explore-search__input"
          type="search"
          placeholder="Search entities — config keys, functions, files…"
          value={q}
          onChange={e => setQ(e.target.value)}
          onFocus={() => results.length && setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
          aria-label="Entity search"
          aria-autocomplete="list"
          aria-expanded={open}
          aria-controls="explore-search-results"
        />
        {loading && <span className="explore-search__spinner" aria-hidden="true" />}
      </div>
      {open && (
        <ul
          id="explore-search-results"
          className="explore-search__results"
          role="listbox"
          aria-label="Search results"
        >
          {results.map(r => (
            <li
              key={r.id}
              role="option"
              className="explore-search__result"
              onMouseDown={() => pick(r)}
            >
              <span className="explore-search__result-name">{r.name}</span>
              <span className={`explore-search__result-type explore-search__result-type--${r.type.toLowerCase()}`}>
                {r.type}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

/* ── Filter chips ─────────────────────────────────────────── */
function FilterChips({ label, options, active, toggle, colorFn }) {
  return (
    <div className="filter-group">
      <span className="filter-group__label">{label}</span>
      <div className="filter-group__chips">
        {options.map(opt => (
          <button
            key={opt}
            className={`filter-chip ${active.has(opt) ? 'filter-chip--active' : ''}`}
            onClick={() => toggle(opt)}
            type="button"
            aria-pressed={active.has(opt)}
          >
            {colorFn && (
              <i className="filter-chip__dot" style={{ background: colorFn(opt) }} aria-hidden="true" />
            )}
            {opt.toLowerCase()}
          </button>
        ))}
      </div>
    </div>
  )
}

/* ── Decision timeline strip ──────────────────────────────── */
function DecisionTimeline({ decisions }) {
  if (!decisions || decisions.length === 0) return null
  const sorted = [...decisions].sort((a, b) =>
    (a.decided_on ?? '').localeCompare(b.decided_on ?? '')
  )
  return (
    <div className="decision-timeline" aria-label="Decision timeline for this entity">
      <h4 className="decision-timeline__title">Decision history</h4>
      <ol className="decision-timeline__list">
        {sorted.map(d => (
          <li key={d.id} className={`decision-timeline__item decision-timeline__item--${d.status.toLowerCase()}`}>
            <span className="decision-timeline__dot" aria-hidden="true" />
            <span className="decision-timeline__date">{(d.decided_on ?? '?').slice(0, 10)}</span>
            <span className="decision-timeline__title-text">{d.title}</span>
            <Badge
              variant={{ ACTIVE: 'active', SUPERSEDED: 'superseded', REVERSED: 'reversed', UNCERTAIN: 'uncertain' }[d.status] || 'default'}
              size="sm"
            >
              {d.status.toLowerCase()}
            </Badge>
          </li>
        ))}
      </ol>
    </div>
  )
}

/* ── Show-more control ─────────────────────────────────────── */
function TruncationNotice({ total, shown, onShowMore }) {
  return (
    <div className="explore-truncation" role="status">
      <p>
        Showing {shown} of {total} nodes.
        Large graphs are capped at {MAX_NODES} for performance.
      </p>
      <Button variant="secondary" size="sm" onClick={onShowMore}>
        Show all (may be slow)
      </Button>
    </div>
  )
}

/* ── Graph skeleton ─────────────────────────────────────────── */
function GraphSkeleton() {
  return (
    <div className="explore-graph-area explore-graph-area--loading">
      <Skeleton variant="block" height="100%" />
    </div>
  )
}

/* ── Main page ──────────────────────────────────────────────── */
export default function Explore() {
  const [selectedEntity, setSelectedEntity] = useState(null)
  const [graphData, setGraphData]           = useState(null)
  const [loading, setLoading]               = useState(false)
  const [error, setError]                   = useState('')

  // Filter state
  const [typeFilters,   setTypeFilters]   = useState(new Set())
  const [statusFilters, setStatusFilters] = useState(new Set())
  const [showAll, setShowAll]             = useState(false)

  /* Fetch the entity's neighbourhood graph */
  useEffect(() => {
    if (!selectedEntity) return
    setLoading(true)
    setError('')
    setGraphData(null)
    setShowAll(false)

    fetch(`/api/entity/graph?id=${encodeURIComponent(selectedEntity.id)}`)
      .then(r => { if (!r.ok) throw new Error(`${r.status}`); return r.json() })
      .then(data => setGraphData(data))
      .catch(e => setError(`Failed to load graph: ${e.message}`))
      .finally(() => setLoading(false))
  }, [selectedEntity])

  /* Derive decisions for the timeline from graph nodes */
  const decisions = graphData?.nodes?.filter(n => n.type === 'Decision') ?? []

  /* Apply type + status filters */
  const filteredGraph = useCallback(() => {
    if (!graphData) return null
    const hasTypeFilter   = typeFilters.size > 0
    const hasStatusFilter = statusFilters.size > 0

    let nodes = graphData.nodes.filter(n => {
      if (hasTypeFilter && !typeFilters.has(n.type)) return false
      if (hasStatusFilter && n.type === 'Decision' && !statusFilters.has(n.status)) return false
      return true
    })

    const nodeIds = new Set(nodes.map(n => n.id))
    const rels = graphData.rels.filter(r => nodeIds.has(r.from) && nodeIds.has(r.to))

    // Cap at MAX_NODES unless showAll
    const total  = nodes.length
    const capped = !showAll && total > MAX_NODES
    if (capped) nodes = nodes.slice(0, MAX_NODES)

    return { nodes, rels, total, capped }
  }, [graphData, typeFilters, statusFilters, showAll])

  const toggleType = useCallback((t) => {
    setTypeFilters(prev => {
      const next = new Set(prev)
      next.has(t) ? next.delete(t) : next.add(t)
      return next
    })
  }, [])

  const toggleStatus = useCallback((s) => {
    setStatusFilters(prev => {
      const next = new Set(prev)
      next.has(s) ? next.delete(s) : next.add(s)
      return next
    })
  }, [])

  const filtered = filteredGraph()

  const statusColors = { ACTIVE: '#3fb950', SUPERSEDED: '#d29922', REVERSED: '#f85149', UNCERTAIN: '#d2a838' }

  return (
    <div className="explore-shell">
      <div className="explore-header container">
        <h1 className="explore-title">Explore the graph</h1>
        <p className="explore-subtitle">
          Search for a code entity to see the decisions that govern it, the commits that changed it, and the people behind it.
        </p>
        <EntitySearch onSelect={setSelectedEntity} />
      </div>

      {selectedEntity && (
        <div className="explore-body container">
          {/* Filters */}
          <div className="explore-filters">
            <FilterChips
              label="Node type"
              options={NODE_TYPES}
              active={typeFilters}
              toggle={toggleType}
            />
            <FilterChips
              label="Decision status"
              options={STATUS_TYPES}
              active={statusFilters}
              toggle={toggleStatus}
              colorFn={s => statusColors[s]}
            />
            {(typeFilters.size > 0 || statusFilters.size > 0) && (
              <button
                className="explore-clear-btn"
                onClick={() => { setTypeFilters(new Set()); setStatusFilters(new Set()) }}
                type="button"
              >
                Clear filters
              </button>
            )}
          </div>

          <div className="explore-content">
            {/* Graph area */}
            <div className="explore-graph-area">
              {loading && <GraphSkeleton />}
              {error && (
                <div className="explore-error" role="alert">
                  <p>{error}</p>
                  <Button variant="ghost" size="sm" onClick={() => setSelectedEntity({ ...selectedEntity })}>
                    Retry
                  </Button>
                </div>
              )}
              {!loading && !error && filtered && (
                <>
                  {filtered.capped && (
                    <TruncationNotice
                      total={filtered.total}
                      shown={filtered.nodes.length}
                      onShowMore={() => setShowAll(true)}
                    />
                  )}
                  {filtered.nodes.length === 0 ? (
                    <div className="explore-empty-graph">
                      <p>No nodes match the current filters.</p>
                    </div>
                  ) : (
                    <Suspense fallback={<GraphSkeleton />}>
                      <GraphView
                        graph={filtered}
                        height="580px"
                      />
                    </Suspense>
                  )}
                </>
              )}
              {!loading && !error && !filtered && selectedEntity && (
                <div className="explore-empty-graph" aria-live="polite">
                  <p>No graph data for <strong>{selectedEntity.name}</strong>.</p>
                </div>
              )}
            </div>

            {/* Sidebar: timeline */}
            <aside className="explore-sidebar" aria-label="Entity details">
              <div className="explore-entity-card">
                <div className="explore-entity-card__type">{selectedEntity.type}</div>
                <h2 className="explore-entity-card__name">{selectedEntity.name}</h2>
                <p className="explore-entity-card__id">{selectedEntity.id}</p>
              </div>

              {loading && (
                <div className="explore-sidebar__loading">
                  <Skeleton variant="text" />
                  <Skeleton variant="text" width="70%" />
                  <Skeleton variant="text" width="50%" />
                </div>
              )}

              {!loading && decisions.length > 0 && (
                <DecisionTimeline decisions={decisions} />
              )}

              {!loading && !error && filtered && decisions.length === 0 && (
                <p className="explore-sidebar__empty">No decisions found for this entity.</p>
              )}
            </aside>
          </div>
        </div>
      )}

      {!selectedEntity && (
        <div className="explore-landing container">
          <p className="explore-landing__hint">
            Start by searching for an entity above — a config key like <code>repl-backlog-size</code>,
            a function like <code>replicationCron</code>, or a file like <code>src/replication.c</code>.
          </p>
        </div>
      )}
    </div>
  )
}
