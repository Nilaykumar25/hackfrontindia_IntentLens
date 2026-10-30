# IntentLens — Final Build Summary

Generated: 2026-10-30 06:22 UTC

## Node Counts

| Label | Count |
|-------|------:|
| Commit | 1372 |
| PullRequest | 321 |
| Issue | 43 |
| Comment | 8502 |
| Document | 2478 |
| Decision | 570 |
| Person | 554 |
| File | 4 |
| Function | 282 |
| ConfigKey | 222 |
| **TOTAL** | **14348** |

## Relationship Counts

| Type | Count |
|------|------:|
| EVIDENCED_BY | 860 |
| GOVERNS | 673 |
| MODIFIES | 4546 |
| PART_OF | 81 |
| AUTHORED | 10188 |
| SUPERSEDES | 18 |
| REFINES | 40 |
| REVERTS | 0 |
| DESCRIBES | 304 |
| COMMENTED_ON | 8502 |
| MADE_BY | 779 |
| REFERENCES | 1215 |
| CLOSES | 43 |
| **TOTAL** | **27249** |

## Decisions by Status

| Status | Count |
|--------|------:|
| ACTIVE | 556 |
| SUPERSEDED | 14 |

## Decisions by Source Kind

| Source Kind | Count |
|-------------|------:|
| pr_or_commit | 503 |
| document | 67 |

## Supersession / Refinement Edges

| Type | Count |
|------|------:|
| SUPERSEDES | 18 |
| REFINES | 40 |
| REVERTS | 0 |

## 5 Example Questions and Results

| # | Question | Entity | Result | Confidence | Decision |
|---|----------|--------|--------|------------|----------|
| 1 | Why was repl-diskless-sync set to yes by default in Redis 7. | `config:repl-diskless-sync` | **ANSWERED** | Medium (0.65) | Comment out repl-compression related configs in re |
| 2 | Why does Redis use a shared global replication buffer instea | `fn:src/replication.c::feedReplicationBuffer` | **ANSWERED** | High (0.82) | Verify TLS server identity by default in redis-cli |
| 3 | Why does Redis replicate key expiry as absolute millisecond  | `fn:src/replication.c::replicationFeedSlave` | **ANSWERED** | High (0.77) | Add key_count field to redisDb for O(1) DBSIZE and |
| 4 | What is the rationale for the Multi-Part AOF mechanism intro | `appenddirname` | **ANSWERED** | High (0.78) | Always create base AOF file when redis starts from |
| 5 | Why does the WAITAOF command exist and how does it differ fr | `fn:src/replication.c::waitCommand` | **ANSWERED** | Low (0.39) | Separate last_offset and last_numreplicas for WAIT |


## Result States

- **ANSWERED** — decision found, confidence ≥ Low, answer generated with evidence citations
- **SUPERSEDED** — decision found but has been replaced; newer decision shown
- **REFUSED** — no governing decision found or confidence below threshold

All 5 questions returned answers in this run (5 × ANSWERED).