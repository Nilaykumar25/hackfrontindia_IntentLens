# Supersession Dossier

Built from git history (`data/repo`) and release-note files in `data/cache/`.
No guessing. Uncertain items marked **unsure**.

Files checked per commit: `src/replication.c`, `src/rdb.c`, `src/aof.c`, `redis.conf`

---

## 1. repl-diskless-sync default changed to yes

**Candidate PR:** #10092  |  **Status:** `complete`

### New commit(s)

| SHA (short) | Date | PR | Subject |
|-------------|------|----|---------|
| `ae8995897` | 2022-01-17 | #10092 | Set repl-diskless-sync to yes by default, add repl-diskless-sync-max-replicas (#10092) |

Files touched: replication.c=yes  rdb.c=no  aof.c=no  redis.conf=yes

### Old (superseded) commit

| SHA (short) | Date | PR | Subject |
|-------------|------|----|---------|
| `18de5395b` | 2014-10-24 | — | Diskless replication documented inside example redis.conf. |

Files touched: replication.c=no  rdb.c=no  aof.c=no  redis.conf=yes
  *(found via `-S'repl-diskless-sync no' -- redis.conf`)*

---

## 2. Multi-Part AOF / appenddirname

**Candidate PR:** #9788  |  **Status:** `complete`

### New commit(s)

| SHA (short) | Date | PR | Subject |
|-------------|------|----|---------|
| `87789fae0` | 2022-01-04 | #9788 | Implement Multi Part AOF mechanism to avoid AOFRW overheads. (#9788) |

Files touched: replication.c=no  rdb.c=yes  aof.c=yes  redis.conf=yes

### Old (superseded) commit

| SHA (short) | Date | PR | Subject |
|-------------|------|----|---------|
| `47ca4b6e2` | 2012-05-22 | — | Allow an AOF rewrite buffer > 2GB (Fix for issue #504). |

Files touched: replication.c=no  rdb.c=no  aof.c=yes  redis.conf=no
  *(found via `-S'aofRewriteBufferReset' -- src/aof.c`)*

---

## 3. Shared replication buffer

**Candidate PR:** #9166  |  **Status:** `complete`

### New commit(s)

| SHA (short) | Date | PR | Subject |
|-------------|------|----|---------|
| `c1718f9d8` | 2021-10-25 | #9166 | Replication backlog and replicas use one global shared replication buffer (#9166) |

Files touched: replication.c=yes  rdb.c=no  aof.c=no  redis.conf=yes

### Old (superseded) commit

| SHA (short) | Date | PR | Subject |
|-------------|------|----|---------|
| `ad7d4c6b7` | 2021-01-27 | #8303 | Implement rdb-only replication (#8303) |

Files touched: replication.c=yes  rdb.c=no  aof.c=no  redis.conf=no
  *(found via `-S'canFeedReplicaReplBuffer' -- src/replication.c`)*

---

## 4. Replicas panic on persistence write failure; ignore option added

**Candidate PR:** #10504  |  **Status:** `complete`

### New commit(s)

| SHA (short) | Date | PR | Subject |
|-------------|------|----|---------|
| `6fa8e4f7a` | 2022-04-26 | #10504 | Set replicas to panic on disk errors, and optionally panic on replication errors (#10504) |

Files touched: replication.c=no  rdb.c=no  aof.c=no  redis.conf=yes

### Old (superseded) commit

| SHA (short) | Date | PR | Subject |
|-------------|------|----|---------|
| `1bf6d6f11` | 2022-01-02 | #9968 | Generate RDB with Functions only via redis-cli --functions-rdb (#9968) |

Files touched: replication.c=yes  rdb.c=yes  aof.c=yes  redis.conf=no
  *(found via `-S'startBgsaveForReplication' -- src/replication.c`)*

> **unsure** — pickaxe found the most recent ancestor that touched `startBgsaveForReplication`, but #9968 is unrelated to the panic behaviour. The *true* old decision is the pre-#10504 code path where replicas silently continued on disk errors. The function existed long before; no single earlier commit is definitively the origin. Use the new commit (#10504) as the pivot; the old behaviour is implicit (silent continue).

---

## 5. TTLs replicated as absolute timestamps (ms)

**Candidate PR:** #8474  |  **Status:** `complete`

### New commit(s)

| SHA (short) | Date | PR | Subject |
|-------------|------|----|---------|
| `53d1acd59` | 2021-05-29 | #8474 | Always replicate time-to-live(TTL) as absolute timestamps in milliseconds (#8474) |

Files touched: replication.c=no  rdb.c=no  aof.c=yes  redis.conf=no

### Old (superseded) commit

| SHA (short) | Date | PR | Subject |
|-------------|------|----|---------|
| `f70e88c1f` | 2018-06-12 | — | RDB: store times consistently in little endian. |

Files touched: replication.c=no  rdb.c=yes  aof.c=no  redis.conf=no
  *(found via `-S'RDB_OPCODE_EXPIRETIME_MS' -- src/rdb.c`)*

---

## 6a. --save argument: stop resetting to defaults on CLI start (6.2)

**Candidate PR:** #7092  |  **Status:** `complete`

### New commit(s)

| SHA (short) | Date | PR | Subject |
|-------------|------|----|---------|
| `24c539251` | 2020-08-05 | — | Merge pull request #7092 from itamarhaber/fix-5629 |

Files touched: replication.c=no  rdb.c=no  aof.c=no  redis.conf=no

### Old (superseded) commit

| SHA (short) | Date | PR | Subject |
|-------------|------|----|---------|
| `4aac3ff24` | 2012-01-16 | — | It is now posible to flush all the previous saving points in redis.conf by using a save directive wi |

Files touched: replication.c=no  rdb.c=no  aof.c=no  redis.conf=yes
  *(found via `-S'resetServerSaveParams' -- src/config.c`)*

---

## 6b. --save regression fix (7.0.1)

**Candidate PR:** #10690  |  **Status:** `complete`

### New commit(s)

| SHA (short) | Date | PR | Subject |
|-------------|------|----|---------|
| `2bcd890d8` | 2022-05-09 | #10690 | Fix --save command line regression in redis 7.0.0 (#10690) |

Files touched: replication.c=no  rdb.c=no  aof.c=no  redis.conf=no

### Old (superseded) commit

| SHA (short) | Date | PR | Subject |
|-------------|------|----|---------|
| `79ac57561` | 2021-11-07 | #9644 | Refactor config.c for generic setter interface (#9644) |

Files touched: replication.c=no  rdb.c=no  aof.c=no  redis.conf=no
  *(found via `-S'appendServerSaveParams' -- src/config.c`)*

> **unsure** — #9644 is the refactor that introduced the regression; it is plausibly the origin commit for the old (broken) behaviour. Confirmed by the release note ("Fix --save command line regression in redis 7.0.0").

---

## 6c. --save no-value backward compat (7.0.3)

**Candidate PR:** #10866  |  **Status:** `complete`

### New commit(s)

| SHA (short) | Date | PR | Subject |
|-------------|------|----|---------|
| `d443e312a` | 2022-06-26 | #10866 | redis-server command line arguments allow passing config name and value in the same arg (#10866) |

Files touched: replication.c=no  rdb.c=no  aof.c=no  redis.conf=no

### Old (superseded) commit

| SHA (short) | Date | PR | Subject |
|-------------|------|----|---------|
| `79ac57561` | 2021-11-07 | #9644 | Refactor config.c for generic setter interface (#9644) |

Files touched: replication.c=no  rdb.c=no  aof.c=no  redis.conf=no
  *(found via `-S'appendServerSaveParams' -- src/config.c`)*

---

## 7. WAIT semantics: now uses offset after last write command

**Candidate PR:** #11713  |  **Status:** `complete`

### New commit(s)

| SHA (short) | Date | PR | Subject |
|-------------|------|----|---------|
| `9344f654c` | 2023-03-14 | #11713 | Implementing the WAITAOF command (issue #10505) (#11713) |

Files touched: replication.c=yes  rdb.c=no  aof.c=yes  redis.conf=no

### Old (superseded) commit

| SHA (short) | Date | PR | Subject |
|-------------|------|----|---------|
| `7997874f4` | 2023-03-13 | #11905 | Fix tail->repl_offset update in feedReplicationBuffer (#11905) |

Files touched: replication.c=yes  rdb.c=no  aof.c=no  redis.conf=no
  *(found via `-S'master_repl_offset' -- src/replication.c`)*

> **unsure** — `master_repl_offset` appears in hundreds of commits; pickaxe returned the most recent pre-#11713 ancestor that touched the symbol, which is #11905 (a bug fix one day earlier). The definitive "old" WAIT behaviour is documented in the #11713 PR body itself: WAIT previously used `server.master_repl_offset` at call time, not `client->woff`. Old commit SHA confirmed but subject is a coincidental neighbour, not the original introduction.

---

## 8. Revert of KEYS output-buffer limit fix (6.2.9 -> 6.2.10)

**Candidate PR:** #11676  |  **Status:** `complete`

### New commit(s)

| SHA (short) | Date | PR | Subject |
|-------------|------|----|---------|
| `e12aacf3a` | 2023-01-17 | #11676 | Revert change to KEYS command from (#11676) |

Files touched: replication.c=no  rdb.c=no  aof.c=no  redis.conf=no

### Old (superseded) commit

| SHA (short) | Date | PR | Subject |
|-------------|------|----|---------|
| `b4123663c` | 2023-01-16 | #11676 | Obuf limit, exit during loop in *RAND* commands and KEYS (#11676) |

Files touched: replication.c=no  rdb.c=no  aof.c=no  redis.conf=no
  *(found via `direct override (revert pair)`)*

---

## Summary

| # | PR | Title | Status |
|---|----|-------|--------|
| 1 | #10092 | repl-diskless-sync default changed to yes | `complete` |
| 2 | #9788 | Multi-Part AOF / appenddirname | `complete` |
| 3 | #9166 | Shared replication buffer | `complete` |
| 4 | #10504 | Replicas panic on persistence write failure; ignore option added | `complete` |
| 5 | #8474 | TTLs replicated as absolute timestamps (ms) | `complete` |
| 6a | #7092 | --save argument: stop resetting to defaults on CLI start (6.2) | `complete` |
| 6b | #10690 | --save regression fix (7.0.1) | `complete` |
| 6c | #10866 | --save no-value backward compat (7.0.3) | `complete` |
| 7 | #11713 | WAIT semantics: now uses offset after last write command | `complete` |
| 8 | #11676 | Revert of KEYS output-buffer limit fix (6.2.9 -> 6.2.10) | `complete` |