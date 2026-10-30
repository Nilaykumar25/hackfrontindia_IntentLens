# Question Verification Results

Five example questions asked via `POST /ask` after the full build.

| # | Question | Entity | Result | Confidence | Decision |
|---|----------|--------|--------|------------|----------|
| 1 | Why was repl-diskless-sync set to yes by default in Redis 7. | `config:repl-diskless-sync` | **ANSWERED** | Medium (0.65) | Comment out repl-compression related configs in re |
| 2 | Why does Redis use a shared global replication buffer instea | `fn:src/replication.c::feedReplicationBuffer` | **ANSWERED** | High (0.82) | Verify TLS server identity by default in redis-cli |
| 3 | Why does Redis replicate key expiry as absolute millisecond  | `fn:src/replication.c::replicationFeedSlave` | **ANSWERED** | High (0.77) | Add key_count field to redisDb for O(1) DBSIZE and |
| 4 | What is the rationale for the Multi-Part AOF mechanism intro | `appenddirname` | **ANSWERED** | High (0.78) | Always create base AOF file when redis starts from |
| 5 | Why does the WAITAOF command exist and how does it differ fr | `fn:src/replication.c::waitCommand` | **ANSWERED** | Low (0.39) | Separate last_offset and last_numreplicas for WAIT |

Answered: 5  Superseded: 0  Refused: 0  Error: 0

## Detail

### Q1: Why was repl-diskless-sync set to yes by default in Redis 7.0?
- **Entity**: `config:repl-diskless-sync`
- **Status**: answered  confidence=Medium (0.65)
- **Decision**: Comment out repl-compression related configs in redis.conf
- **Superseded notice**: This decision replaced: “Add zstd compression for replication with IO-threads only” (2026-06-24).
- **Answer**: repl-diskless-sync was set to yes by default in Redis 7.0 because redis is built with repl compression disabled by default, and the related configs needed to be commented out in redis.conf. [E1]
- **Evidence kinds**: ['Commit']

### Q2: Why does Redis use a shared global replication buffer instead of per-replica buffers?
- **Entity**: `fn:src/replication.c::feedReplicationBuffer`
- **Status**: answered  confidence=High (0.82)
- **Decision**: Verify TLS server identity by default in redis-cli, redis-benchmark, and Sentinel
- **Answer**: Redis tools verify TLS server identity by default to prevent unauthorized server impersonation and credential interception. [E1] The change rejects certificates that do not match the dialed host or configured expected peer name. [E1] The previous beh
- **Evidence kinds**: ['Commit']

### Q3: Why does Redis replicate key expiry as absolute millisecond timestamps?
- **Entity**: `fn:src/replication.c::replicationFeedSlave`
- **Status**: answered  confidence=High (0.77)
- **Decision**: Add key_count field to redisDb for O(1) DBSIZE and expires computation
- **Answer**: A key_count field is added to redisDb to track the total number of keys, enabling O(1) DBSIZE and O(1) expires computation. [E1] The key_count field avoids scanning all dictionaries and summing up their sizes in a loop, which would be O(slot count). 
- **Evidence kinds**: ['PullRequest']

### Q4: What is the rationale for the Multi-Part AOF mechanism introduced in Redis 7.0?
- **Entity**: `appenddirname`
- **Status**: answered  confidence=High (0.78)
- **Decision**: Always create base AOF file when redis starts from empty
- **Answer**: The mechanism forces creation of a BASE AOF file when Redis starts from an empty dataset to ensure persistence modules can access configuration metadata. [E1] Normally, after running for some time and undergoing AOF rewrites, a base rdb file is alway
- **Evidence kinds**: ['Commit']

### Q5: Why does the WAITAOF command exist and how does it differ from WAIT?
- **Entity**: `fn:src/replication.c::waitCommand`
- **Status**: answered  confidence=Low (0.39)
- **Decision**: Separate last_offset and last_numreplicas for WAITAOF to prevent WAITAOF from being wrongly unblocke
- **Answer**: WAITAOF exists to wait for AOF replication to a specific offset and replica count independently of WAIT, requiring separate tracking variables. [E1] The old code incorrectly mixed last_offset and last_numreplicas across WAIT and WAITAOF conditions. [
- **Evidence kinds**: ['PullRequest']