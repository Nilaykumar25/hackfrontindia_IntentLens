import { useEffect, useRef, useState } from 'react'

/**
 * EvidenceThread — the signature animated SVG motif.
 *
 * Shows 5 nodes in a horizontal-diagonal layout connected by
 * thin lines that draw in left-to-right with staggered 150ms
 * offsets and 600ms duration per edge.
 *
 * @param {string|number} [width='100%']
 * @param {boolean} [animated=true]
 * @param {'sm'|'md'|'lg'} [size='md']
 * @param {boolean} [decorative=false] — sets aria-hidden when true
 */
export default function EvidenceThread({
  width = '100%',
  animated = true,
  size = 'md',
  decorative = false,
}) {
  const prefersReduced = useRef(
    typeof window !== 'undefined'
      ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
      : false
  )

  const shouldAnimate = animated && !prefersReduced.current

  const dims = { sm: 280, md: 520, lg: 760 }
  const svgW = dims[size] ?? 520
  const svgH = size === 'sm' ? 80 : size === 'lg' ? 140 : 110

  // Node positions (x, y) — horizontal diagonal layout
  const nodes = [
    { id: 'entity',   x: 48,          y: svgH * 0.65, color: 'var(--entity)',      label: 'replication.c', labelAnchor: 'middle' },
    { id: 'decision', x: svgW * 0.28, y: svgH * 0.28, color: 'var(--accent)',      label: 'Decision',      labelAnchor: 'middle' },
    { id: 'discuss',  x: svgW * 0.50, y: svgH * 0.65, color: 'var(--muted)',       label: 'PR #1234',      labelAnchor: 'middle' },
    { id: 'person',   x: svgW * 0.72, y: svgH * 0.28, color: 'var(--muted)',       label: 'antirez',       labelAnchor: 'middle' },
    { id: 'date',     x: svgW - 48,   y: svgH * 0.65, color: 'var(--muted)',       label: '2019-03-15',    labelAnchor: 'middle' },
  ]

  const edges = [
    { from: 0, to: 1, delay: 0 },
    { from: 1, to: 2, delay: 150 },
    { from: 2, to: 3, delay: 300 },
    { from: 3, to: 4, delay: 450 },
  ]

  const r = size === 'sm' ? 5 : size === 'lg' ? 10 : 7
  const fontSize = size === 'sm' ? 9 : size === 'lg' ? 13 : 11
  const labelOffset = r + 14

  // Track which labels are visible (appear after their incoming edge draws)
  const [labelVisible, setLabelVisible] = useState(
    shouldAnimate ? [true, false, false, false, false] : [true, true, true, true, true]
  )

  useEffect(() => {
    if (!shouldAnimate) return
    // node[0] label visible immediately; nodes 1–4 appear after their edge draws in
    edges.forEach(({ to, delay }) => {
      const totalDelay = delay + 600
      const timer = setTimeout(() => {
        setLabelVisible(prev => {
          const next = [...prev]
          next[to] = true
          return next
        })
      }, totalDelay)
      return () => clearTimeout(timer)
    })
  }, [shouldAnimate]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <svg
      width={width}
      viewBox={`0 0 ${svgW} ${svgH}`}
      aria-label={decorative ? undefined : 'Evidence trail: code entity connected to decision, discussion, person, and date'}
      aria-hidden={decorative ? 'true' : undefined}
      role={decorative ? 'presentation' : 'img'}
      style={{ overflow: 'visible', display: 'block' }}
    >
      {/* ── Edges ── */}
      {edges.map(({ from, to, delay }) => {
        const n1 = nodes[from]
        const n2 = nodes[to]
        const dx = n2.x - n1.x
        const dy = n2.y - n1.y
        const len = Math.sqrt(dx * dx + dy * dy)

        return (
          <line
            key={`edge-${from}-${to}`}
            x1={n1.x}
            y1={n1.y}
            x2={n2.x}
            y2={n2.y}
            stroke="var(--line)"
            strokeWidth="1.5"
            strokeLinecap="round"
            style={shouldAnimate ? {
              strokeDasharray: len,
              strokeDashoffset: len,
              animation: `thread-draw 600ms var(--ease-out) ${delay}ms forwards`,
            } : undefined}
          />
        )
      })}

      {/* ── Nodes ── */}
      {nodes.map((n, i) => (
        <g key={n.id}>
          {/* Outer glow ring for entity and decision */}
          {(n.id === 'entity' || n.id === 'decision') && (
            <circle
              cx={n.x}
              cy={n.y}
              r={r + 4}
              fill={n.id === 'entity' ? 'var(--entity-soft)' : 'var(--accent-soft)'}
            />
          )}
          <circle
            cx={n.x}
            cy={n.y}
            r={r}
            fill={n.color}
            opacity={n.id === 'entity' || n.id === 'decision' ? 1 : 0.65}
          />

          {/* Label */}
          <text
            x={n.x}
            y={n.id === 'decision' || n.id === 'person' ? n.y - labelOffset : n.y + labelOffset + fontSize}
            textAnchor={n.labelAnchor}
            fontSize={fontSize}
            fontFamily="var(--font-ui)"
            fill={n.id === 'entity' ? 'var(--entity)' : n.id === 'decision' ? 'var(--accent)' : 'var(--muted)'}
            fontWeight={n.id === 'entity' || n.id === 'decision' ? '500' : '400'}
            style={shouldAnimate ? {
              opacity: labelVisible[i] ? 1 : 0,
              transition: 'opacity 300ms var(--ease-out)',
            } : undefined}
          >
            {n.label}
          </text>
        </g>
      ))}

      {/* ── Keyframes injected inline ── */}
      <defs>
        <style>{`
          @keyframes thread-draw {
            to { stroke-dashoffset: 0; }
          }
        `}</style>
      </defs>
    </svg>
  )
}
