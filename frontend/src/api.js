export async function ask(question, lang = 'en') {
  const r = await fetch('/api/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, lang }),
  })
  if (!r.ok) throw new Error(`The server returned ${r.status}. Check that the backend is running and AuraDB is reachable.`)
  return r.json()
}

/** Alias — matches the task spec naming */
export const askQuestion = ask

export async function getStats() {
  try {
    const r = await fetch('/api/stats')
    if (!r.ok) return null
    return r.json()
  } catch {
    return null
  }
}

export async function searchEntities(q) {
  if (!q) return []
  const r = await fetch(`/api/entities/search?q=${encodeURIComponent(q)}`)
  if (!r.ok) return []
  return r.json()
}

/**
 * getEntityGraph — fetch graph data for a single entity
 * GET /api/entity/graph?id=...&expand=true
 */
export async function getEntityGraph(id, expand = false) {
  const params = new URLSearchParams({ id })
  if (expand) params.set('expand', 'true')
  const r = await fetch(`/api/entity/graph?${params.toString()}`)
  if (!r.ok) throw new Error(`Server error ${r.status}`)
  return r.json()
}

export async function getEvalResults() {
  const r = await fetch('/api/eval/results')
  if (r.status === 404) return null
  if (!r.ok) throw new Error(`Server error ${r.status}`)
  return r.json()
}
