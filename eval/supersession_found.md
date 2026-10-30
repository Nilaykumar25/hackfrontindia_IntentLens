# Supersession Edges Found

Total edges: 58

| Type | Conf | Newer (date) | Older (date) | Reason |
|------|------|--------------|--------------|--------|
| REFINES | 1.00 | Allow absolute oom-score-adj values and  (2020-11-22) | Fix oom-score-adj-values range and add a (2020-11-22) | NEWER repeats the same two fixes with clearer wording and adds the +2000 offset  |
| REFINES | 0.95 | Remove temporary AOF and RDB files in a  (2020-10-13) | Remove temporary rdb file in background  (2020-09-17) | NEWER extends OLDER from RDB-only to include AOF files while keeping the same ba |
| REFINES | 0.95 | Fix double free in stream consumer PEL l (2026-04-22) | Add guard for duplicate stream consumer  (2026-04-22) | NEWER adjusts the duplicate consumer handling to avoid double free by relying on |
| REFINES | 0.95 | Introduce maxmemory-eviction-tenacity co (2020-09-15) | Add time-limited eviction with maxmemory (2020-09-15) | NEWER adds the maxmemory-eviction-tenacity config to OLDER's time-limited evicti |
| REFINES | 0.95 | Revert multi OOM limit and add multi buf (2024-01-25) | Revert #5454 and add multi buffer limit (2024-01-18) | NEWER replaces the OOM-blocking condition with an unconditional client-level lim |
| REFINES | 0.90 | Don't send REPLCONF ACK to old masters (2014-01-08) | Introduce REPLCONF internal command for  (2012-06-26) | NEWER extends the REPLCONF command to handle ACK responses for backward compatib |
| REFINES | 0.90 | Don't expire keys while loading RDB from (2018-05-29) | Enable RDB-preamble rewriting by default (2018-03-25) | NEWER adjusts the RDB preamble loading process to prevent key expirations, prese |
| REFINES | 0.90 | Adjust active defrag defaults and behavi (2019-11-10) | Change default active-defrag-cycle-min t (2018-02-18) | NEWER narrows the default effort range and adds mid-run reset behavior, building |
| REFINES | 0.90 | Use libsystemd's sd_notify for communica (2019-04-27) | Add supervised configuration option for  (2015-01-08) | NEWER replaces internal sd_notify replication with systemd's libsystemd, extendi |
| REFINES | 0.90 | Add `tls-expected-peer-name-allow-parent (2026-08-21) | Add opt-in tls-expected-peer-name for TL (2026-07-20) | NEWER adds an optional gating parameter to control a specific behavior (parent-d |
| REFINES | 0.90 | Track config-load depth to prevent dupli (2026-08-27) | Log parent-domain advisory on first TLS  (2026-08-26) | NEWER adds config-load depth tracking to prevent duplicate warnings from nested  |
| REFINES | 0.90 | Log parent-domain advisory on first TLS  (2026-08-26) | Add `tls-expected-peer-name-allow-parent (2026-08-21) | NEWER extends OLDER's parent-domain warning to startup/enable-time, not just con |
| REFINES | 0.90 | Deduplicate parent-domain advisory acros (2026-08-27) | Track config-load depth to prevent dupli (2026-08-27) | NEWER extends the deduplication logic to cover TLS config triggers, building on  |
| REFINES | 0.90 | Trigger AOFRW immediately on AOF preload (2026-07-14) | preload-file format is aof:<path> or rdb (2026-07-09) | NEWER extends OLDER by adding an AOFRW trigger requirement after AOF preload to  |
| REFINES | 0.90 | Move preload AOF setup before applyAppen (2026-07-22) | Install preload-file data as local AOF w (2026-07-22) | NEWER adjusts the timing of the preload AOF setup to prevent unnecessary rewrite |
| REFINES | 0.90 | Call fsync on directory when installing  (2026-07-23) | Install preload-file data as local AOF w (2026-07-22) | NEWER adds a directory fsync to the existing preload-file AOF installation proce |
| REFINES | 0.90 | Opt-in automatic conversion via configur (2026-06-24) | Introduce hinted hash templates for memo (2026-06-24) | NEWER adds automatic opt-in thresholds to the existing template encoding, extend |
| REFINES | 0.90 | Introduce flushdb option for repl-diskle (2025-12-01) | repl-diskless-load default 'swapdb' (2022-09-11) | NEWER adds a new option that extends the existing repl-diskless-load behavior wi |
| REFINES | 0.90 | Best-effort compensation for client memo (2024-12-22) | Add maxmemory-clients eviction mechanism (2021-03-23) | NEWER adjusts the eviction logic to handle delayed memory updates without changi |
| REFINES | 0.90 | Main thread as first IO thread; low io-t (2024-12-22) | Async IO threads with event-driven model (2024-12-22) | NEWER adjusts the thread model by making main thread the first IO thread, narrow |
| REFINES | 0.90 | Change default value of always-show-logo (2020-09-03) | Only show Redis logo if logging to stdou (2016-12-19) | NEWER adjusts the default value of an existing option to match code behavior, wi |
| REFINES | 0.90 | Allow absolute oom-score-adj values and  (2020-11-22) | oom-score-adj default disabled (2020-11-22) | NEWER extends OLDER by adding absolute-value support and fixing initialization o |
| REFINES | 0.90 | Implement Multi-Part AOF mechanism to av (2022-01-04) | Implement Multi-Part AOF with manifest-b (2021-11-16) | NEWER retains the core BASE/INCR/manifest design but adds failure rate limiting  |
| REFINES | 0.90 | Add propagation-error-behavior config fo (2022-04-26) | Add `propagation-error-behavior` config  (2022-04-26) | NEWER clarifies that the config controls panicking on command failures during re |
| REFINES | 0.90 | Add listpack encoding for list (2022-11-17) | Add listpack encoding for list (2022-11-16) | NEWER adds dynamic conversion between listpack and quicklist based on size thres |
| REFINES | 0.90 | Check AOF_FSYNC_ALWAYS in flushAppendOnl (2023-03-29) | Flush AOF before processing events while (2022-04-11) | NEWER extends OLDER by adding AOF_FSYNC_ALWAYS checks in flushAppendOnlyFile to  |
| REFINES | 0.90 | Call emptyData when disk-based sync rdbL (2024-01-18) | Change return value of rdbLoad to enums (2022-07-26) | NEWER adds a cleanup action for rdbLoad failures without changing the enum retur |
| REFINES | 0.85 | Use replicationFeedSlaves() to send PING (2012-11-03) | Send async PING before starting replicat (2012-08-31) | NEWER preserves the async PING intent but changes the implementation mechanism t |
| REFINES | 0.85 | Re-emit SELECT after each new slave full (2015-08-05) | Trigger BGSAVE after diskless-to-disk co (2014-10-16) | NEWER adjusts BGSAVE timing to fix offset correctness, building on the OLDER BGS |
| REFINES | 0.85 | Remove temporary rdb file in background  (2020-09-17) | Avoid snprintf in rdbRemoveTempFile for  (2020-09-17) | NEWER builds on OLDER's async-signal-safety concern by moving deletion to a back |
| REFINES | 0.85 | Update fsynced_reploff_pending even if t (2023-09-28) | Check AOF_FSYNC_ALWAYS in flushAppendOnl (2023-03-29) | NEWER extends OLDER by adding another condition to flushAppendOnlyFile for handl |
| REFINES | 0.85 | Filter expired IDMP entries during RDB s (2026-03-16) | Don't expire keys when loading an RDB af (2012-01-13) | NEWER extends OLDER by adding expiration filtering for IDMP entries on both save |
| REFINES | 0.80 | Apply rdbLoadMillisecondTime() fix only  (2018-06-12) | Don't expire keys when loading an RDB af (2012-01-13) | NEWER narrows the scope of OLDER by applying the fix only to new RDB versions wh |
| REFINES | 0.80 | Use pipe for diskless replication RDB tr (2019-08-11) | Avoid simultaneous RDB and AOF child pro (2016-07-21) | NEWER adjusts the RDB saving mechanism by using a pipe and moving socket writes  |
| REFINES | 0.80 | Use compilation-time error for unsupport (2026-08-06) | Add tls-groups configuration for TLS nam (2026-07-29) | NEWER narrows the scope of OLDER by specifying the build-time error handling str |
| REFINES | 0.80 | Add cluster-announce-tls-port configurat (2021-03-30) | Keep legacy behavior: cluster-announce-p (2021-03-10) | NEWER adds a new option to override TLS-specific announce port without changing  |
| REFINES | 0.80 | UINT opcode for backwards compatibility  (2019-09-05) | module identifier prefix (2019-07-21) | NEWER adds a UINT opcode for backwards compatibility while keeping the MT prefix |
| REFINES | 0.70 | Create module API for forking child proc (2019-07-17) | Avoid simultaneous RDB and AOF child pro (2016-07-21) | NEWER refactors fork tracking to improve reliability, building on the OLDER goal |
| REFINES | 0.70 | RDB channel replication requires repl-di (2025-01-13) | Force filtered RDBs to be sent over sock (2021-12-27) | NEWER adds a conditional fallback to older replication mode when diskless sync i |
| REFINES | 0.70 | Runtime changes to hash-min-template-ent (2026-07-18) | Hashes using field expiration are never  (2026-07-18) | NEWER extends OLDER by adding lazy, one-way runtime changes to template conversi |
| SUPERSEDES | 1.00 | Hashes using field expiration are never  (2026-07-18) | Template encoding is one-way and never c (2026-07-18) | NEWER prevents hashes with field expiration from being converted to template enc |
| SUPERSEDES | 1.00 | Rollback rdbLoadObject() to load all fie (2024-06-16) | Don't expire keys when loading an RDB af (2012-01-13) | NEWER explicitly reverts a modification made to rdbLoadObject() that was related |
| SUPERSEDES | 1.00 | Default behavior: fail to start if reque (2020-10-28) | Add '-' prefix to allow EADDRNOTAVAIL to (2020-10-28) | NEWER reverses the default behavior by failing on EADDRNOTAVAIL instead of silen |
| SUPERSEDES | 1.00 | ACL channels permission handling for sav (2021-04-19) | Add pub/sub channel patterns to ACL with (2020-12-01) | NEWER mandates resetchannels for ACL SAVE, overriding OLDER's plan to change acl |
| SUPERSEDES | 1.00 | Add max-new-connections-per-cycle and ma (2024-01-03) | Split into two separate configs with dif (2023-12-12) | NEWER replaces the split TCP/TLS configs with a single max-new-connections-per-c |
| SUPERSEDES | 0.95 | Use RDB info fields for user info with b (2019-03-02) | Introduce RDB AUX fields (2015-01-08) | NEWER explicitly rejects introducing new prefixed fields, overriding OLDER's app |
| SUPERSEDES | 0.95 | Conditional memrev64ifbe() call based on (2026-05-13) | Conditionally fix signed integer loading (2026-05-13) | NEWER changes the version threshold from >=9 to >=5, directly contradicting the  |
| SUPERSEDES | 0.95 | Template encoding is one-way and never c (2026-07-18) | Opt-in automatic conversion via configur (2026-06-24) | NEWER explicitly reverses OLDER's opt-in threshold behavior by making template e |
| SUPERSEDES | 0.90 | Delay BGSAVE only when AOF rewriting is  (2016-07-22) | Avoid simultaneous RDB and AOF child pro (2016-07-21) | NEWER replaces the always-1-second BGSAVE delay with a conditional delay only du |
| SUPERSEDES | 0.90 | Make disconnectSlaves() synchronous in t (2020-05-22) | Fix #7306 less aggressively (2020-05-22) | NEWER makes disconnectSlaves() synchronous, directly reversing OLDER's decision  |
| SUPERSEDES | 0.90 | Remove dbid parameter from rdbLoadObject (2024-05-12) | Remove dbid parameter from rdbLoadObject (2024-05-08) | NEWER explicitly reverses OLDER's rationale by keeping dbid in the signature as  |
| SUPERSEDES | 0.90 | Remove dbid parameter from rdbLoadObject (2024-05-12) | Remove dbid parameter from rdbLoadObject (2024-05-12) | NEWER removes the dbid parameter from all call sites, while OLDER only proposed  |
| SUPERSEDES | 0.90 | Keep defrag effort constant during a sca (2024-01-31) | Reduce default active defrag minimum and (2019-11-10) | NEWER overrides OLDER's approach of dynamically lowering effort when fragmentati |
| SUPERSEDES | 0.90 | Deprecate aggregate save config line beh (2021-12-01) | Support variadic save directive in confi (2021-11-07) | NEWER explicitly deprecates the aggregate save config line behavior that OLDER i |
| SUPERSEDES | 0.90 | Comment out repl-compression related con (2026-07-20) | Add zstd compression for replication wit (2026-06-24) | NEWER comments out repl-compression configs because it is disabled by default, d |
| SUPERSEDES | 0.90 | hash-rdb-load-min-template-entries defau (2026-07-18) | Opt-in automatic conversion via configur (2026-06-24) | NEWER overrides OLDER's default-enabled opt-in by setting default 0 to disable c |
| SUPERSEDES | 0.80 | Rollback rdbLoadObject() to load all fie (2024-06-16) | Remove debug parameter from rdbLoadObjec (2024-05-15) | NEWER reverts a previous modification to rdbLoadObject(), directly reversing the |
| SUPERSEDES | 0.80 | Replace ziplist with listpack for t_hash (2021-08-10) | Convert all ziplists to listpacks on RDB (2021-07-05) | NEWER explicitly replaces ziplist with listpack for t_hash encoding, overriding  |

## Detail

### [1] REFINES  confidence=1.000
**Newer** `80d53677`  2020-11-22T13:57:56+02:00  [ACTIVE]  Allow absolute oom-score-adj values and fix config file initialization order
**Older** `5e76eda2`  2020-11-22  [ACTIVE]  Fix oom-score-adj-values range and add absolute values option
Reason: NEWER repeats the same two fixes with clearer wording and adds the +2000 offset rationale, refining the explanation without changing the decision.

### [2] REFINES  confidence=0.950
**Newer** `be41bee0`  2020-10-13  [ACTIVE]  Remove temporary AOF and RDB files in a background thread
**Older** `5a56bd51`  2020-09-17T23:20:10+08:00  [ACTIVE]  Remove temporary rdb file in background thread using bg_unlink
Reason: NEWER extends OLDER from RDB-only to include AOF files while keeping the same background thread approach.

### [3] REFINES  confidence=0.950
**Newer** `852a24ae`  2026-04-22  [ACTIVE]  Fix double free in stream consumer PEL loading by avoiding explicit streamFreeNACK on shared nack
**Older** `391bb409`  2026-04-22  [ACTIVE]  Add guard for duplicate stream consumer PEL NACK assignment
Reason: NEWER adjusts the duplicate consumer handling to avoid double free by relying on cgroup->pel cleanup, building on OLDER's corruption detection.

### [4] REFINES  confidence=0.950
**Newer** `4cec3c18`  2020-09-15  [ACTIVE]  Introduce maxmemory-eviction-tenacity config for incremental eviction
**Older** `d746c1ea`  2020-09-15  [ACTIVE]  Add time-limited eviction with maxmemory-eviction-tenacity
Reason: NEWER adds the maxmemory-eviction-tenacity config to OLDER's time-limited eviction to mitigate specific edge cases like massive pipelined MGET, narrowing the scope without discarding the original appr

### [5] REFINES  confidence=0.950
**Newer** `2d438922`  2024-01-25T17:17:39+08:00  [ACTIVE]  Revert multi OOM limit and add multi buffer limit
**Older** `9e799c22`  2024-01-18  [ACTIVE]  Revert #5454 and add multi buffer limit
Reason: NEWER replaces the OOM-blocking condition with an unconditional client-level limit, refining the approach without contradicting the core goal.

### [6] REFINES  confidence=0.900
**Newer** `975f0ed4`  2014-01-08  [ACTIVE]  Don't send REPLCONF ACK to old masters
**Older** `863ef41b`  2012-06-26T09:47:47+02:00  [ACTIVE]  Introduce REPLCONF internal command for slave-to-master configuration exchange
Reason: NEWER extends the REPLCONF command to handle ACK responses for backward compatibility, adjusting the original implementation without replacing it.

### [7] REFINES  confidence=0.900
**Newer** `05659292`  2018-05-29T12:37:39+02:00  [ACTIVE]  Don't expire keys while loading RDB from AOF preamble
**Older** `24a69160`  2018-03-25  [ACTIVE]  Enable RDB-preamble rewriting by default in AOF
Reason: NEWER adjusts the RDB preamble loading process to prevent key expirations, preserving consistency with the AOF tail, without reversing the default RDB preamble rewriting choice.

### [8] REFINES  confidence=0.900
**Newer** `561737bf`  2019-11-10  [ACTIVE]  Adjust active defrag defaults and behavior when disabled mid-run
**Older** `cb5ed2e8`  2018-02-18  [ACTIVE]  Change default active-defrag-cycle-min to induce lower latency
Reason: NEWER narrows the default effort range and adds mid-run reset behavior, building on the original latency reduction goal.

### [9] REFINES  confidence=0.900
**Newer** `cb99bc8c`  2019-04-27T18:07:30+02:00  [ACTIVE]  Use libsystemd's sd_notify for communicating redis status to systemd
**Older** `2e665382`  2015-01-08T15:22:33-05:00  [ACTIVE]  Add supervised configuration option for redis processes
Reason: NEWER replaces internal sd_notify replication with systemd's libsystemd, extending the earlier supervised configuration option.

### [10] REFINES  confidence=0.900
**Newer** `c82603f5`  2026-08-21  [ACTIVE]  Add `tls-expected-peer-name-allow-parent-domain` to gate parent-domain matching
**Older** `74e97bb4`  2026-07-20  [ACTIVE]  Add opt-in tls-expected-peer-name for TLS peer certificate name verification
Reason: NEWER adds an optional gating parameter to control a specific behavior (parent-domain matching) within the broader OLDER TLS peer name verification feature.

### [11] REFINES  confidence=0.900
**Newer** `b673c6ab`  2026-08-27  [ACTIVE]  Track config-load depth to prevent duplicate startup warnings from `include`
**Older** `5d2ec6a5`  2026-08-26  [ACTIVE]  Log parent-domain advisory on first TLS configuration in addition to config-time validation
Reason: NEWER adds config-load depth tracking to prevent duplicate warnings from nested includes, extending the original single-warning approach without reversing it.

### [12] REFINES  confidence=0.900
**Newer** `5d2ec6a5`  2026-08-26  [ACTIVE]  Log parent-domain advisory on first TLS configuration in addition to config-time validation
**Older** `c82603f5`  2026-08-21  [ACTIVE]  Add `tls-expected-peer-name-allow-parent-domain` to gate parent-domain matching
Reason: NEWER extends OLDER's parent-domain warning to startup/enable-time, not just config-time.

### [13] REFINES  confidence=0.900
**Newer** `ca601b6b`  2026-08-27  [ACTIVE]  Deduplicate parent-domain advisory across CONFIG SET and TLS enable
**Older** `b673c6ab`  2026-08-27  [ACTIVE]  Track config-load depth to prevent duplicate startup warnings from `include`
Reason: NEWER extends the deduplication logic to cover TLS config triggers, building on the existing depth tracking.

### [14] REFINES  confidence=0.900
**Newer** `2d2c97ef`  2026-07-14  [ACTIVE]  Trigger AOFRW immediately on AOF preload to prevent memory/disk mismatch
**Older** `de1751a0`  2026-07-09  [ACTIVE]  preload-file format is aof:<path> or rdb:<path>
Reason: NEWER extends OLDER by adding an AOFRW trigger requirement after AOF preload to ensure consistency, without changing the preload-file format.

### [15] REFINES  confidence=0.900
**Newer** `a548ee56`  2026-07-22  [ACTIVE]  Move preload AOF setup before applyAppendOnlyConfig
**Older** `59e50c16`  2026-07-22  [ACTIVE]  Install preload-file data as local AOF without rewrite
Reason: NEWER adjusts the timing of the preload AOF setup to prevent unnecessary rewrites when appendonly is turned off, refining the original approach without discarding it.

### [16] REFINES  confidence=0.900
**Newer** `5ba8b8f7`  2026-07-23  [ACTIVE]  Call fsync on directory when installing preload files
**Older** `59e50c16`  2026-07-22  [ACTIVE]  Install preload-file data as local AOF without rewrite
Reason: NEWER adds a directory fsync to the existing preload-file AOF installation process without changing the core approach.

### [17] REFINES  confidence=0.900
**Newer** `65acf7fc`  2026-06-24  [SUPERSEDED]  Opt-in automatic conversion via configuration thresholds
**Older** `c0e8bd34`  2026-06-24  [ACTIVE]  Introduce hinted hash templates for memory-efficient hash sharing
Reason: NEWER adds automatic opt-in thresholds to the existing template encoding, extending its applicability without changing the core encoding.

### [18] REFINES  confidence=0.900
**Newer** `de21ef36`  2025-12-01  [ACTIVE]  Introduce flushdb option for repl-diskless-load
**Older** `9df2ced8`  2022-09-11  [ACTIVE]  repl-diskless-load default 'swapdb'
Reason: NEWER adds a new option that extends the existing repl-diskless-load behavior without replacing the swapdb default.

### [19] REFINES  confidence=0.900
**Newer** `03028d1a`  2024-12-22  [ACTIVE]  Best-effort compensation for client memory usage before eviction
**Older** `9d656035`  2021-03-23  [ACTIVE]  Add maxmemory-clients eviction mechanism
Reason: NEWER adjusts the eviction logic to handle delayed memory updates without changing the maxmemory-clients mechanism itself.

### [20] REFINES  confidence=0.900
**Newer** `f9aca75e`  2024-12-22  [ACTIVE]  Main thread as first IO thread; low io-threads may not improve simple command performance
**Older** `ddfeaea5`  2024-12-22  [ACTIVE]  Async IO threads with event-driven model and independent event loops per thread
Reason: NEWER adjusts the thread model by making main thread the first IO thread, narrowing OLDER's independent event loops design without discarding it.

### [21] REFINES  confidence=0.900
**Newer** `a5b70aa1`  2020-09-03  [ACTIVE]  Change default value of always-show-logo
**Older** `64021ab9`  2016-12-19T16:41:47+01:00  [ACTIVE]  Only show Redis logo if logging to stdout / TTY
Reason: NEWER adjusts the default value of an existing option to match code behavior, without changing the option's purpose.

### [22] REFINES  confidence=0.900
**Newer** `80d53677`  2020-11-22T13:57:56+02:00  [ACTIVE]  Allow absolute oom-score-adj values and fix config file initialization order
**Older** `0a8333fa`  2020-11-22  [ACTIVE]  oom-score-adj default disabled
Reason: NEWER extends OLDER by adding absolute-value support and fixing initialization order, not reversing the default choice.

### [23] REFINES  confidence=0.900
**Newer** `c9f91a9f`  2022-01-04  [ACTIVE]  Implement Multi-Part AOF mechanism to avoid AOFRW overheads
**Older** `205874c1`  2021-11-16  [ACTIVE]  Implement Multi-Part AOF with manifest-based file management
Reason: NEWER retains the core BASE/INCR/manifest design but adds failure rate limiting and disable-auto-gc options.

### [24] REFINES  confidence=0.900
**Newer** `2dd37203`  2022-04-26  [ACTIVE]  Add propagation-error-behavior config for replication errors
**Older** `b9e992ad`  2022-04-26  [ACTIVE]  Add `propagation-error-behavior` config to control replica/AOF panic on command errors
Reason: NEWER clarifies that the config controls panicking on command failures during replication or AOF-loading, refining the scope of OLDER.

### [25] REFINES  confidence=0.900
**Newer** `3bf9ee03`  2022-11-17  [ACTIVE]  Add listpack encoding for list
**Older** `059118f7`  2022-11-16  [ACTIVE]  Add listpack encoding for list
Reason: NEWER adds dynamic conversion between listpack and quicklist based on size thresholds, extending the static listpack-only approach.

### [26] REFINES  confidence=0.900
**Newer** `85e2a26e`  2023-03-29T20:17:05+08:00  [ACTIVE]  Check AOF_FSYNC_ALWAYS in flushAppendOnlyFile to handle appendfsync mode changes
**Older** `7ad37608`  2022-04-11T16:08:39+08:00  [ACTIVE]  Flush AOF before processing events while blocked for appendfsync=always
Reason: NEWER extends OLDER by adding AOF_FSYNC_ALWAYS checks in flushAppendOnlyFile to handle appendfsync mode changes, building on the same persistence concern.

### [27] REFINES  confidence=0.900
**Newer** `30a0277d`  2024-01-18T22:28:52+08:00  [ACTIVE]  Call emptyData when disk-based sync rdbLoad fails
**Older** `473a4279`  2022-07-26  [ACTIVE]  Change return value of rdbLoad to enums
Reason: NEWER adds a cleanup action for rdbLoad failures without changing the enum return value approach from OLDER.

### [28] REFINES  confidence=0.850
**Newer** `0bddad9f`  2012-11-03  [ACTIVE]  Use replicationFeedSlaves() to send PING to slaves
**Older** `0510f8e9`  2012-08-31T15:32:57+02:00  [ACTIVE]  Send async PING before starting replication with master
Reason: NEWER preserves the async PING intent but changes the implementation mechanism to a standard interface for consistency.

### [29] REFINES  confidence=0.850
**Newer** `67d70b2c`  2015-08-05  [ACTIVE]  Re-emit SELECT after each new slave full sync setup
**Older** `a0a9a3d7`  2014-10-16T10:15:18+02:00  [ACTIVE]  Trigger BGSAVE after diskless-to-disk config change
Reason: NEWER adjusts BGSAVE timing to fix offset correctness, building on the OLDER BGSAVE triggering mechanism.

### [30] REFINES  confidence=0.850
**Newer** `5a56bd51`  2020-09-17T23:20:10+08:00  [ACTIVE]  Remove temporary rdb file in background thread using bg_unlink
**Older** `ffd1de81`  2020-09-17  [ACTIVE]  Avoid snprintf in rdbRemoveTempFile for async-signal-safety
Reason: NEWER builds on OLDER's async-signal-safety concern by moving deletion to a background thread, extending the safety improvement without reversing it.

### [31] REFINES  confidence=0.850
**Newer** `9ffcd45f`  2023-09-28  [ACTIVE]  Update fsynced_reploff_pending even if there's nothing to fsync
**Older** `85e2a26e`  2023-03-29T20:17:05+08:00  [ACTIVE]  Check AOF_FSYNC_ALWAYS in flushAppendOnlyFile to handle appendfsync mode changes
Reason: NEWER extends OLDER by adding another condition to flushAppendOnlyFile for handling fsync-related state updates.

### [32] REFINES  confidence=0.850
**Newer** `4bd67454`  2026-03-16T09:04:28+02:00  [ACTIVE]  Filter expired IDMP entries during RDB save and load
**Older** `a4ad1387`  2012-01-13  [SUPERSEDED]  Don't expire keys when loading an RDB after a SYNC
Reason: NEWER extends OLDER by adding expiration filtering for IDMP entries on both save and load, building upon the original principle of preventing expired key issues during RDB operations.

### [33] REFINES  confidence=0.800
**Newer** `3403fa68`  2018-06-12T18:21:39+02:00  [ACTIVE]  Apply rdbLoadMillisecondTime() fix only for new RDB versions
**Older** `a4ad1387`  2012-01-13  [SUPERSEDED]  Don't expire keys when loading an RDB after a SYNC
Reason: NEWER narrows the scope of OLDER by applying the fix only to new RDB versions while preserving compatibility for old ones.

### [34] REFINES  confidence=0.800
**Newer** `185c9bba`  2019-08-11T16:07:53+03:00  [ACTIVE]  Use pipe for diskless replication RDB transfer and write sockets from parent process
**Older** `41ba1a39`  2016-07-21T18:34:53+02:00  [ACTIVE]  Avoid simultaneous RDB and AOF child process
Reason: NEWER adjusts the RDB saving mechanism by using a pipe and moving socket writes to the parent, refining the OLDER decision to avoid simultaneous child processes.

### [35] REFINES  confidence=0.800
**Newer** `2966e220`  2026-08-06  [ACTIVE]  Use compilation-time error for unsupported OpenSSL versions
**Older** `b5299def`  2026-07-29  [ACTIVE]  Add tls-groups configuration for TLS named group selection
Reason: NEWER narrows the scope of OLDER by specifying the build-time error handling strategy for unsupported OpenSSL versions.

### [36] REFINES  confidence=0.800
**Newer** `db7ff50c`  2021-03-30T22:11:32+02:00  [ACTIVE]  Add cluster-announce-tls-port configuration option
**Older** `13cf3e9d`  2021-03-10  [ACTIVE]  Keep legacy behavior: cluster-announce-port defaults to TLS port in TLS cluster
Reason: NEWER adds a new option to override TLS-specific announce port without changing the default TLS port behavior from OLDER.

### [37] REFINES  confidence=0.800
**Newer** `4875c972`  2019-09-05  [ACTIVE]  UINT opcode for backwards compatibility in write 'when'
**Older** `642df0ee`  2019-07-21  [ACTIVE]  module identifier prefix
Reason: NEWER adds a UINT opcode for backwards compatibility while keeping the MT prefix approach from OLDER.

### [38] REFINES  confidence=0.700
**Newer** `51aacad9`  2019-07-17T08:51:02+03:00  [ACTIVE]  Create module API for forking child processes and refactor AOF/RDB fork tracking
**Older** `41ba1a39`  2016-07-21T18:34:53+02:00  [ACTIVE]  Avoid simultaneous RDB and AOF child process
Reason: NEWER refactors fork tracking to improve reliability, building on the OLDER goal of controlling child processes without contradicting it.

### [39] REFINES  confidence=0.700
**Newer** `e04d5418`  2025-01-13T12:09:52Z  [ACTIVE]  RDB channel replication requires repl-diskless-sync
**Older** `daa5ec7d`  2021-12-27  [ACTIVE]  Force filtered RDBs to be sent over sockets (diskless replication)
Reason: NEWER adds a conditional fallback to older replication mode when diskless sync is disabled, extending the OLDER forced socket-only approach with backward compatibility.

### [40] REFINES  confidence=0.700
**Newer** `a634b981`  2026-07-18  [ACTIVE]  Runtime changes to hash-min-template-entries are lazy and one-way
**Older** `ab7f7bea`  2026-07-18  [ACTIVE]  Hashes using field expiration are never converted to template encoding
Reason: NEWER extends OLDER by adding lazy, one-way runtime changes to template conversion, building on the stable field set principle.

### [41] SUPERSEDES  confidence=1.000
**Newer** `ab7f7bea`  2026-07-18  [ACTIVE]  Hashes using field expiration are never converted to template encoding
**Older** `4d62d34a`  2026-07-18  [SUPERSEDED]  Template encoding is one-way and never converted back
Reason: NEWER prevents hashes with field expiration from being converted to template encoding, overriding the one-way conversion rule in OLDER.

### [42] SUPERSEDES  confidence=1.000
**Newer** `4403388d`  2024-06-16  [ACTIVE]  Rollback rdbLoadObject() to load all fields of empty hash regardless of expiration
**Older** `a4ad1387`  2012-01-13  [SUPERSEDED]  Don't expire keys when loading an RDB after a SYNC
Reason: NEWER explicitly reverts a modification made to rdbLoadObject() that was related to expiration handling during RDB load, overriding the previous behavior.

### [43] SUPERSEDES  confidence=1.000
**Newer** `534e0ff3`  2020-10-28T21:09:15+02:00  [ACTIVE]  Default behavior: fail to start if requested bind address is not available
**Older** `ae048388`  2020-10-28  [SUPERSEDED]  Add '-' prefix to allow EADDRNOTAVAIL to be ignored by default
Reason: NEWER reverses the default behavior by failing on EADDRNOTAVAIL instead of silently ignoring it, directly opposing the OLDER decision's default of ignoring the error.

### [44] SUPERSEDES  confidence=1.000
**Newer** `e34d0cba`  2021-04-19  [ACTIVE]  ACL channels permission handling for save/load scenario
**Older** `c953f5ba`  2020-12-01  [SUPERSEDED]  Add pub/sub channel patterns to ACL with & symbol
Reason: NEWER mandates resetchannels for ACL SAVE, overriding OLDER's plan to change acl-pubsub-default to resetchannels only in the next major version.

### [45] SUPERSEDES  confidence=1.000
**Newer** `c998244d`  2024-01-03T01:15:03+02:00  [ACTIVE]  Add max-new-connections-per-cycle and max-new-tls-connections-per-cycle configurations
**Older** `530d10d3`  2023-12-12  [SUPERSEDED]  Split into two separate configs with different defaults for TCP and TLS
Reason: NEWER replaces the split TCP/TLS configs with a single max-new-connections-per-cycle, reversing OLDER's separate default values.

### [46] SUPERSEDES  confidence=0.950
**Newer** `88bbfede`  2019-03-02T21:17:40+01:00  [ACTIVE]  Use RDB info fields for user info with backward-compatible naming
**Older** `a203891c`  2015-01-08T08:56:35+01:00  [ACTIVE]  Introduce RDB AUX fields
Reason: NEWER explicitly rejects introducing new prefixed fields, overriding OLDER's approach of adding new aux fields.

### [47] SUPERSEDES  confidence=0.950
**Newer** `caa6ce06`  2026-05-13  [ACTIVE]  Conditional memrev64ifbe() call based on RDB version
**Older** `1b0446ce`  2026-05-13  [SUPERSEDED]  Conditionally fix signed integer loading for RDB versions ≥ 9 only
Reason: NEWER changes the version threshold from >=9 to >=5, directly contradicting the specific version cutoff in OLDER.

### [48] SUPERSEDES  confidence=0.950
**Newer** `4d62d34a`  2026-07-18  [SUPERSEDED]  Template encoding is one-way and never converted back
**Older** `65acf7fc`  2026-06-24  [SUPERSEDED]  Opt-in automatic conversion via configuration thresholds
Reason: NEWER explicitly reverses OLDER's opt-in threshold behavior by making template encoding one-way, preventing reversion even when field count drops below threshold.

### [49] SUPERSEDES  confidence=0.900
**Newer** `47184fa6`  2016-07-22  [ACTIVE]  Delay BGSAVE only when AOF rewriting is active
**Older** `41ba1a39`  2016-07-21T18:34:53+02:00  [ACTIVE]  Avoid simultaneous RDB and AOF child process
Reason: NEWER replaces the always-1-second BGSAVE delay with a conditional delay only during AOF rewriting.

### [50] SUPERSEDES  confidence=0.900
**Newer** `da527e34`  2020-05-22T19:29:09+02:00  [ACTIVE]  Make disconnectSlaves() synchronous in the base case
**Older** `229166de`  2020-05-22  [ACTIVE]  Fix #7306 less aggressively
Reason: NEWER makes disconnectSlaves() synchronous, directly reversing OLDER's decision to call it asynchronously from freeClient().

### [51] SUPERSEDES  confidence=0.900
**Newer** `f0149b16`  2024-05-12  [SUPERSEDED]  Remove dbid parameter from rdbLoadObject() signature
**Older** `63b5f88c`  2024-05-08  [SUPERSEDED]  Remove dbid parameter from rdbLoadObject()
Reason: NEWER explicitly reverses OLDER's rationale by keeping dbid in the signature as NULL and questioning the removal, while OLDER stated dbid can be extracted from db.

### [52] SUPERSEDES  confidence=0.900
**Newer** `dfb3e4a8`  2024-05-12  [ACTIVE]  Remove dbid parameter from rdbLoadObject() call sites
**Older** `f0149b16`  2024-05-12  [SUPERSEDED]  Remove dbid parameter from rdbLoadObject() signature
Reason: NEWER removes the dbid parameter from all call sites, while OLDER only proposed removing it from the signature and passing NULL.

### [53] SUPERSEDES  confidence=0.900
**Newer** `9c13b8c2`  2024-01-31  [ACTIVE]  Keep defrag effort constant during a scan unless configuration changes
**Older** `a5acd6d0`  2019-11-10  [SUPERSEDED]  Reduce default active defrag minimum and maximum effort
Reason: NEWER overrides OLDER's approach of dynamically lowering effort when fragmentation drops, instead keeping effort constant during a sweep.

### [54] SUPERSEDES  confidence=0.900
**Newer** `31ae5821`  2021-12-01  [ACTIVE]  Deprecate aggregate save config line behavior
**Older** `91aa1796`  2021-11-07T11:40:09Z  [SUPERSEDED]  Support variadic save directive in config file
Reason: NEWER explicitly deprecates the aggregate save config line behavior that OLDER introduced as a feature.

### [55] SUPERSEDES  confidence=0.900
**Newer** `addf61ee`  2026-07-20  [ACTIVE]  Comment out repl-compression related configs in redis.conf
**Older** `98079177`  2026-06-24  [SUPERSEDED]  Add zstd compression for replication with IO-threads only
Reason: NEWER comments out repl-compression configs because it is disabled by default, directly reversing OLDER's introduction of zstd compression for replication.

### [56] SUPERSEDES  confidence=0.900
**Newer** `07489921`  2026-07-18  [ACTIVE]  hash-rdb-load-min-template-entries default 0
**Older** `65acf7fc`  2026-06-24  [SUPERSEDED]  Opt-in automatic conversion via configuration thresholds
Reason: NEWER overrides OLDER's default-enabled opt-in by setting default 0 to disable conversion on RDB load.

### [57] SUPERSEDES  confidence=0.800
**Newer** `4403388d`  2024-06-16  [ACTIVE]  Rollback rdbLoadObject() to load all fields of empty hash regardless of expiration
**Older** `7565ac6a`  2024-05-15  [SUPERSEDED]  Remove debug parameter from rdbLoadObject()
Reason: NEWER reverts a previous modification to rdbLoadObject(), directly reversing the HFE feature change that OLDER had removed.

### [58] SUPERSEDES  confidence=0.800
**Newer** `47eed37d`  2021-08-10T14:18:49+08:00  [ACTIVE]  Replace ziplist with listpack for t_hash encoding
**Older** `cc47cd02`  2021-07-05  [SUPERSEDED]  Convert all ziplists to listpacks on RDB loading time
Reason: NEWER explicitly replaces ziplist with listpack for t_hash encoding, overriding the OLDER approach of converting ziplists to listpacks only during RDB loading.