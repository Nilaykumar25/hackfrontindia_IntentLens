import { useEffect, useState } from 'react'
import { getStats } from '../api.js'
import './StatsStrip.css'

const STAT_DEFS = [
  { key: 'commits',    label: 'Commits ingested' },
  { key: 'decisions',  label: 'Decisions mined' },
  { key: 'superseded', label: 'Superseded decisions' },
  { key: 'persons',    label: 'Contributors tracked' },
  { key: 'entities',   label: 'Code entities' },
]

function fmt(n) {
  if (n == null) return '—'
  if (n >= 1000) return (n / 1000).toFixed(1).replace(/\.0$/, '') + 'k'
  return String(n)
}

/**
 * StatsStrip — live counts from GET /stats.
 * Shows a quiet empty state if the API is down or returns zero data.
 * NEVER shows fake or placeholder numbers.
 */
export default function StatsStrip() {
  const [stats, setStats] = useState(null)  // null = loading
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    getStats()
      .then(data => {
        if (!data || Object.values(data).every(v => v === 0)) {
          setFailed(true)
        } else {
          setStats(data)
        }
      })
      .catch(() => setFailed(true))
  }, [])

  /* Quiet empty state if API is down or graph not loaded */
  if (failed) {
    return (
      <div className="stats-strip stats-strip--empty" aria-label="Live graph statistics unavailable">
        <p className="stats-strip__empty-msg">
          Graph statistics will appear here once data is loaded.
          Run <code>make ingest && make build</code> to populate.
        </p>
      </div>
    )
  }

  return (
    <div
      className="stats-strip"
      aria-label="Live graph statistics"
      aria-live="polite"
    >
      {STAT_DEFS.map(({ key, label }) => (
        <div key={key} className="stats-strip__item">
          <span className="stats-strip__value">
            {stats ? fmt(stats[key]) : <span className="stats-strip__loading" aria-hidden="true" />}
          </span>
          <span className="stats-strip__label">{label}</span>
        </div>
      ))}
    </div>
  )
}
