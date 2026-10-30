/**
 * GraphView — NVL 0.3.9 wrapper
 *
 * API verified from source:
 *   - mouseEventCallbacks.onNodeClick(node, hitElements, event)
 *   - mouseEventCallbacks.onCanvasClick(event)
 *   - nodes: [{id, caption, color, size}]
 *   - rels:  [{id, from, to, caption}]
 *
 * The wrapper renders inside whatever div it is placed in.
 * The parent MUST have an explicit height (set via className or style).
 */
import { useState, useCallback } from 'react'
import { InteractiveNvlWrapper } from '@neo4j-nvl/react'
import Badge from './Badge.jsx'
import './GraphView.css'

// Status → colour mapping matches design tokens
const STATUS_COLORS = {
  ACTIVE:    '#3fb950',
  SUPERSEDED:'#d29922',
  REVERSED:  '#f85149',
  UNCERTAIN: '#d2a838',
}
const TYPE_COLORS = {
  Decision:    '#e8a838',
  Entity:      '#58a6ff',
  ConfigKey:   '#58a6ff',
  Function:    '#58a6ff',
  File:        '#58a6ff',
  Commit:      '#6e7681',
  PullRequest: '#6e7681',
  Issue:       '#6e7681',
  Comment:     '#8b949e',
  Document:    '#6e7681',
  Person:      '#bc8cff',
}

function nodeColor(n) {
  if (n.type === 'Decision') return STATUS_COLORS[n.status] ?? STATUS_COLORS.ACTIVE
  return TYPE_COLORS[n.type] ?? '#6e7681'
}

function nodeSize(n) {
  if (n.type === 'Decision') return 36
  if (n.type === 'Entity' || n.type === 'ConfigKey' || n.type === 'Function' || n.type === 'File') return 32
  return 22
}

function toNvlNodes(nodes) {
  return nodes.map(n => ({
    id: n.id,
    caption: (n.label ?? n.id).slice(0, 40),
    color:   nodeColor(n),
    size:    nodeSize(n),
  }))
}

function toNvlRels(rels) {
  return rels.map((r, i) => {
    const isReview = r.review_flag === 'needs_review'
    return {
      id:      `r${i}`,
      from:    r.from,
      to:      r.to,
      caption: isReview ? `${r.type} ⚠` : r.type,
      // NVL 0.3.9 doesn't support dash styles, so we surface the flag via
      // caption and store it as a custom field for the side panel
      _review_flag: isReview,
    }
  })
}

/* ── Side panel for a selected node ──────────────────────── */
function NodePanel({ node, graph, onClose }) {
  const statusVariant = {
    ACTIVE: 'active', SUPERSEDED: 'superseded', REVERSED: 'reversed', UNCERTAIN: 'uncertain',
  }[node.status] || 'default'

  // Check if any edge involving this node is flagged
  const flaggedEdges = (graph?.rels ?? []).filter(
    r => (r.from === node.id || r.to === node.id) && r.review_flag === 'needs_review'
  )

  return (
    <div className="gv-panel" role="complementary" aria-label="Selected node details">
      <button className="gv-panel__close" onClick={onClose} aria-label="Close panel">×</button>
      <div className="gv-panel__type">{node.type}</div>
      <h3 className="gv-panel__title">{node.label ?? node.id}</h3>
      {node.status && (
        <Badge variant={statusVariant} size="sm" style={{ marginBottom: 'var(--sp-4)' }}>
          {node.status.toLowerCase()}
        </Badge>
      )}
      {flaggedEdges.length > 0 && (
        <div className="gv-panel__review-notice" role="note" title="This node has supersession or refinement links that may be cosmetic rather than genuine reversals">
          <span aria-hidden="true">⚠</span>
          {' '}Unverified link — some edges to/from this node are marked for review.
        </div>
      )}
      <dl className="gv-panel__meta">
        <dt>ID</dt>
        <dd className="gv-panel__mono">{node.id}</dd>
        {node.url && (
          <>
            <dt>Source</dt>
            <dd>
              <a href={node.url} target="_blank" rel="noreferrer noopener" className="gv-panel__link">
                Open ↗
              </a>
            </dd>
          </>
        )}
      </dl>
    </div>
  )
}

/* ── Main component ───────────────────────────────────────── */
export default function GraphView({ graph, height = '100%' }) {
  const [selected, setSelected] = useState(null)

  const handleNodeClick = useCallback((node) => {
    // NVL 0.3.9: onNodeClick receives the NVL node object (has .id)
    const full = graph?.nodes?.find(n => n.id === node.id)
    setSelected(full ?? node)
  }, [graph])

  const handleCanvasClick = useCallback(() => {
    setSelected(null)
  }, [])

  if (!graph || graph.nodes.length === 0) {
    return (
      <div className="gv-empty" style={{ height }}>
        <p>No graph to show.</p>
      </div>
    )
  }

  const nvlNodes = toNvlNodes(graph.nodes)
  const nvlRels  = toNvlRels(graph.rels)

  return (
    <div className="gv-shell" style={{ height }} aria-label="Graph of the decision neighbourhood">
      <div className="gv-canvas">
        <InteractiveNvlWrapper
          nodes={nvlNodes}
          rels={nvlRels}
          nvlOptions={{ initialZoom: 0.8, minZoom: 0.1, maxZoom: 5 }}
          mouseEventCallbacks={{
            onNodeClick:   handleNodeClick,
            onCanvasClick: handleCanvasClick,
            onZoom:  true,
            onPan:   true,
            onDrag:  true,
          }}
        />
      </div>

      {/* Legend */}
      <ul className="gv-legend" aria-label="Graph legend">
        <li><i style={{ background: STATUS_COLORS.ACTIVE }}    />Active</li>
        <li><i style={{ background: STATUS_COLORS.SUPERSEDED }} />Superseded</li>
        <li><i style={{ background: STATUS_COLORS.REVERSED }}  />Reversed</li>
        <li><i style={{ background: TYPE_COLORS.Entity }}      />Entity</li>
        <li><i style={{ background: TYPE_COLORS.Person }}      />Person</li>
      </ul>

      {/* Side panel */}
      {selected && <NodePanel node={selected} graph={graph} onClose={() => setSelected(null)} />}
    </div>
  )
}
