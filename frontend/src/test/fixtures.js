/**
 * Test fixtures — canonical AnswerResponse shapes for all states.
 * Matches the backend AnswerResponse Pydantic model exactly.
 */

export const ANSWERED_FIXTURE = {
  question: 'Why does always-show-logo exist in redis.conf?',
  status: 'answered',
  answer:
    'Redis only shows its logo when logging to stdout or a TTY. [E1] ' +
    'A new always-show-logo option was added so operators can force the logo ' +
    'in startup logs regardless of environment. [E2]',
  decision: {
    id: 'dec-001',
    title: 'Only show Redis logo if logging to stdout / TTY',
    summary:
      'The Redis logo is only displayed when logging to stdout or a TTY. ' +
      'A new option always-show-logo was added to redis.conf.',
    rationale:
      'Avoid cluttering non-interactive log output with the ASCII art logo.',
    alternatives_rejected: ['Always show logo', 'Never show logo'],
    decided_on: '2016-12-19',
    status: 'ACTIVE',
    explicit_rationale: true,
    agreement: 0.92,
  },
  superseded_notice: null,
  replaced_by: null,
  evidence: [
    {
      ref: 'E1',
      id: 'commit-abc123',
      kind: 'Commit',
      url: 'https://github.com/redis/redis/commit/abc123',
      date: '2016-12-19T00:00:00',
      author: 'antirez',
      snippet: 'Add always-show-logo configuration option.',
      quote: 'A new option always-show-logo was added.',
    },
    {
      ref: 'E2',
      id: 'commit-def456',
      kind: 'Commit',
      url: 'https://github.com/redis/redis/commit/def456',
      date: '2016-12-20T00:00:00',
      author: 'antirez',
      snippet: 'Document always-show-logo in redis.conf.',
      quote: 'Document the new option in redis.conf comments.',
    },
  ],
  person_to_ask: {
    id: 'antirez@gmail.com',
    name: 'Salvatore Sanfilippo',
    reason: 'Made or approved this decision',
  },
  history: [],
  confidence: {
    score: 0.799,
    label: 'High',
    factors: {
      directness: 1.0,
      corroboration: 0.7,
      agreement: 0.92,
      currency: 1.0,
      distance: 1.0,
    },
    reasons: [
      'Rationale is stated explicitly in the source.',
      '2 independent source types support this decision.',
      'Two extraction passes agree.',
      'Code still matches the decision.',
      'Directly linked to the entity.',
    ],
  },
  refusal_reason: null,
  related: [],
  graph: {
    nodes: [
      { id: 'dec-001', label: 'Only show Redis logo if logging to stdout / TTY', type: 'Decision', status: 'ACTIVE' },
      { id: 'config:always-show-logo', label: 'always-show-logo', type: 'Entity' },
    ],
    rels: [
      { from: 'dec-001', to: 'config:always-show-logo', type: 'GOVERNS' },
    ],
  },
  latency_ms: 1820,
}

export const SUPERSEDED_FIXTURE = {
  question: 'Why does replicationCron avoid simultaneous BGSAVE and BGREWRITEAOF?',
  status: 'answered',
  answer:
    'Redis delays BGSAVE only when AOF rewriting is currently active. [E1] ' +
    'This replaced an earlier approach that always avoided simultaneous processes.',
  decision: {
    id: 'dec-002',
    title: 'Delay BGSAVE only when AOF rewriting is active',
    summary:
      'Replace the always-1-second BGSAVE delay with a conditional delay ' +
      'that only applies during AOF rewriting.',
    rationale:
      'The unconditional delay was overly conservative and hurt replication ' +
      'performance when no AOF rewriting was happening.',
    alternatives_rejected: ['Keep unconditional 1-second delay'],
    decided_on: '2016-07-22',
    status: 'ACTIVE',
    explicit_rationale: true,
    agreement: 0.88,
  },
  superseded_notice:
    'The closest match, "Avoid simultaneous RDB and AOF child process" ' +
    '(2016-07-21), was superseded on 2016-07-22 by ' +
    '"Delay BGSAVE only when AOF rewriting is active". Showing the current decision.',
  replaced_by: {
    id: 'dec-002',
    title: 'Delay BGSAVE only when AOF rewriting is active',
    decided_on: '2016-07-22',
  },
  evidence: [
    {
      ref: 'E1',
      id: 'commit-bgsave',
      kind: 'Commit',
      url: 'https://github.com/redis/redis/commit/bgsave',
      date: '2016-07-22T00:00:00',
      author: 'antirez',
      snippet: 'Delay BGSAVE only when AOF rewriting is active.',
      quote: 'Replace the always-1-second delay with a conditional one.',
    },
  ],
  person_to_ask: {
    id: 'antirez@gmail.com',
    name: 'Salvatore Sanfilippo',
    reason: 'Most commits to this entity (69); last active 2016-07-22',
  },
  history: [
    {
      id: 'dec-old',
      title: 'Avoid simultaneous RDB and AOF child process',
      decided_on: '2016-07-21',
      status: 'SUPERSEDED',
    },
  ],
  confidence: {
    score: 0.688,
    label: 'Medium',
    factors: {
      directness: 1.0,
      corroboration: 0.4,
      agreement: 0.88,
      currency: 1.0,
      distance: 0.67,
    },
    reasons: [
      'Rationale is stated explicitly in the source.',
      '1 independent source type supports this decision.',
      'Two extraction passes agree.',
      'Code still matches the decision.',
      'Linked to the entity through a looser semantic match.',
    ],
  },
  refusal_reason: null,
  related: [],
  graph: {
    nodes: [
      { id: 'dec-002', label: 'Delay BGSAVE only when AOF rewriting is active', type: 'Decision', status: 'ACTIVE' },
      { id: 'dec-old', label: 'Avoid simultaneous RDB and AOF child process', type: 'Decision', status: 'SUPERSEDED' },
      { id: 'fn:replicationCron', label: 'replicationCron', type: 'Entity' },
    ],
    rels: [
      { from: 'dec-002', to: 'fn:replicationCron', type: 'GOVERNS' },
      { from: 'dec-002', to: 'dec-old', type: 'SUPERSEDES' },
    ],
  },
  latency_ms: 2463,
}

export const REFUSED_FIXTURE = {
  status: 'refused',
  answer: '',
  decision: null,
  superseded_notice: null,
  replaced_by: null,
  evidence: [],
  person_to_ask: {
    id: 'antirez@gmail.com',
    name: 'Salvatore Sanfilippo',
    reason: 'Most commits to this entity',
  },
  history: [],
  confidence: {
    score: 0.0,
    label: 'No answer',
    factors: null,
    reasons: ['No decision in the graph governs the entities named in this question.'],
  },
  refusal_reason: 'No decision in the graph governs the entities named in this question.',
  related: [
    {
      type: 'last_change',
      id: 'commit-abc',
      message: 'Fix SDS string handling in replication context',
      date: '2022-03-14T10:00:00',
      author: 'antirez',
      url: 'https://github.com/redis/redis/commit/abc',
    },
    {
      type: 'discussion',
      id: 'comment-xyz',
      snippet: 'This was discussed in PR #4521 regarding string internals...',
      date: '2021-06-01T00:00:00',
      author: 'yossigo',
      url: 'https://github.com/redis/redis/pull/4521',
    },
  ],
  graph: { nodes: [], rels: [] },
  latency_ms: 39000,
}


/** Fixture with mixed history: one SUPERSEDED (should be struck) + one ACTIVE/refined */
export const MIXED_HISTORY_FIXTURE = {
  question: 'Why does Redis use incremental trimming for the replication backlog?',
  status: 'answered',
  answer:
    'Redis trims the replication backlog incrementally to keep its size close to ' +
    'repl_backlog_size without excessive overhead. [E1]',
  decision: {
    id: 'dec-inc',
    title: 'Trim replication backlog only when a new block is added',
    summary: 'Incremental trimming avoids repeated unnecessary trim attempts on small writes.',
    rationale: 'Avoids repeated unnecessary trimming when small amounts of data are added.',
    alternatives_rejected: [],
    decided_on: '2023-05-14',
    status: 'ACTIVE',
    explicit_rationale: true,
    agreement: 0.95,
  },
  superseded_notice: null,
  replaced_by: null,
  evidence: [
    {
      ref: 'E1',
      id: 'src/replication.c#L634',
      kind: 'Document',
      url: 'https://github.com/redis/redis/blob/main/src/replication.c#L634',
      date: '2023-05-14',
      author: '',
      snippet: 'Trim after adding replication data to keep backlog size close to repl_backlog_size.',
      quote: 'trim after adding replication data to keep the backlog size close to repl_backlog_size',
    },
  ],
  person_to_ask: {
    id: 'antirez@gmail.com',
    name: 'Salvatore Sanfilippo',
    reason: 'Most commits to this entity',
  },
  history: [
    {
      id: 'dec-old-sup',
      title: 'Always trim backlog on every replication write',
      decided_on: '2021-10-01',
      status: 'SUPERSEDED',
    },
    {
      id: 'dec-old-active',
      title: 'Backlog trimming: avoid large node creation',
      decided_on: '2021-09-15',
      status: 'ACTIVE',
    },
  ],
  confidence: {
    score: 0.75,
    label: 'High',
    factors: { directness: 1.0, corroboration: 0.7, agreement: 0.95, currency: 1.0, distance: 1.0 },
    reasons: ['Rationale is stated explicitly in the source.'],
  },
  refusal_reason: null,
  related: [],
  graph: { nodes: [], rels: [] },
  latency_ms: 1200,
}
