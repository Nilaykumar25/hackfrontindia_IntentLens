# Supersession Candidates from Release Notes

Sources: `data/cache/relnotes_7.2.txt`, `relnotes_7.0.txt`, `relnotes_6.2.txt`
(extracted via `git show origin/<branch>:00-RELEASENOTES`)

Supersession markers: **default, deprecated, removed, replaced, no longer, changed**

Scope legend:
- **in-scope** – concerns replication, RDB/AOF persistence, or a redis.conf setting
- **out-scope** – clearly unrelated (Lua, ACL, TLS, cluster key-slots, HLL, …)
- **unsure** – cannot determine scope from this line alone

## Branch 7.2

Total candidates: 8  | in-scope: 1  | unsure: 4  | out-scope: 3

| Line # | Scope | PR(s) | Text |
|--------|-------|-------|------|
| 593 | **in-scope** | #11713 | * WAIT now no longer waits for the replication offset after your last command, |
| 365 | **unsure** | #10536, #12166 | * Cluster SHARD IDs are no longer visible in the cluster nodes output, |
| 368 | **unsure** | #12326 | the order is changed and the reply is sent before the published message (#12326) |
| 569 | **unsure** | #11439 | * Mark the QUIT command as deprecated (#11439) |
| 606 | **unsure** | #11407 | * Use jemalloc by default also on ARM (#11407) |
| 551 | **out-scope** | #11012, #11160 | * Blocked stream command that's released when key no longer exists carries a |
| 555 | **out-scope** | #11012, #11224 | * The way ACL users are stored internally no longer removes redundant command |
| 562 | **out-scope** | #11279 | * ACL default newly created user set sanitize-payload flag in ACL LIST/GETUSER #11279 |

## Branch 7.0

Total candidates: 16  | in-scope: 6  | unsure: 7  | out-scope: 3

| Line # | Scope | PR(s) | Text |
|--------|-------|-------|------|
| 405 | **in-scope** | #10660 | * Omitting a config option value in command line argument no longer works (#10660) |
| 836 | **in-scope** | #9034 | * Modifying the bind parameter to a non-default value will no longer implicitly |
| 868 | **in-scope** | #9034 | default is in use (#9034) |
| 870 | **in-scope** | #10092 | * Config: repl-diskless-sync is now set to yes by default (#10092) |
| 945 | **in-scope** | #9872 | * shutdown-timeout, default 10 seconds (#9872) |
| 951 | **in-scope** | #9462 | * latency-tracking, enabled by default, and latency-tracking-info-percentiles (#9462) |
| 130 | **unsure** | #11319 | * Fix module RM_Call commands failing with OOM when maxmemory is changed to zero (#11319) |
| 579 | **unsure** | #10500 | argument was completely removed (#10500) |
| 628 | **unsure** | #10459 | * BITSET and BITFIELD SET should propagate even if just length changed (#10459) |
| 840 | **unsure** | #9812, #10181 | This has been deprecated and off by default since Redis 6 and is no longer |
| 843 | **in-scope** | #9812 | * SCRIPT LOAD and SCRIPT FLUSH are no longer propagated to replicas / AOF (#9812) |
| 884 | **unsure** | #9920 | * Sensitive configs and commands blocked (protected) by default (#9920) |
| 905 | **unsure** | #9403 | * BITSET and BITFIELD SET only propagated when the value actually changed (#9403) |
| 617 | **out-scope** | #10400 | * Sentinel: Fix no reconnect after auth-pass is changed (#10400) |
| 842 | **out-scope** | #10181 | * ACL: pub/sub channels are blocked by default (acl-pubsub-default=resetchannels) (#10181) |
| 856 | **out-scope** | #9920 | * MODULE and DEBUG commands disabled (protected) by default, for better security (#9920) |

## Branch 6.2

Total candidates: 15  | in-scope: 5  | unsure: 10  | out-scope: 0

| Line # | Scope | PR(s) | Text |
|--------|-------|-------|------|
| 347 | **in-scope** | — | set-max-intset-entries is manually configured to a non-default, very large |
| 358 | **in-scope** | — | configuring a non-default, large value for proto-max-bulk-len and |
| 475 | **in-scope** | — | changing the default set-max-intset-entries configuration value, creating a |
| 504 | **in-scope** | #8719 | * Fix config rewrite with an empty `save` config resulsing in default `save` values (#8719) |
| 851 | **in-scope** | #7936 | * Optionally (default) fail to start if requested bind address is not available (#7936) |
| 342 | **unsure** | — | to a non-default, very large value [reported by yiyuaner]. |
| 354 | **unsure** | — | data types, when configuring a large, non-default value for |
| 367 | **unsure** | #9209 | This actually changed in 6.2.0 but was overlooked and omitted from the release notes. |
| 503 | **unsure** | #8723 | * Fix default user, overwritten and reset users losing pubsub channel permissions (#8723) |
| 518 | **unsure** | #8633 | * Process HELLO command even if the default user has no permissions (#8633) |
| 603 | **unsure** | — | input size. By default, it is 512MB which is a safe value for all platforms. |
| 732 | **unsure** | #8039 | * Tracking clients will no longer receive unnecessary key invalidation messages after FLUSHDB (#8039) |
| 764 | **unsure** | #8224 | affected platforms by default. |
| 824 | **unsure** | #7807, #7993 | Has flags to enable full O(N) validation (disabled by default). |
| 912 | **unsure** | #7644 | * Optionally (not by default) use H/W Monotonic clock for faster time sampling (#7644) |

## Summary

- Total supersession-marker lines across all three branches: **39**
- In-scope (replication / persistence / conf): **13**
- Unsure: **20**
- Out-of-scope: **6**

In-scope candidates (consolidated, deduplicated by text):

| Branch | Line # | PR(s) | Text |
|--------|--------|-------|------|
| 6.2 | 347 | — | set-max-intset-entries is manually configured to a non-default, very large |
| 6.2 | 358 | — | configuring a non-default, large value for proto-max-bulk-len and |
| 6.2 | 475 | — | changing the default set-max-intset-entries configuration value, creating a |
| 6.2 | 504 | #8719 | * Fix config rewrite with an empty `save` config resulsing in default `save` values (#8719) |
| 6.2 | 851 | #7936 | * Optionally (default) fail to start if requested bind address is not available (#7936) |
| 7.0 | 405 | #10660 | * Omitting a config option value in command line argument no longer works (#10660) |
| 7.0 | 836 | #9034 | * Modifying the bind parameter to a non-default value will no longer implicitly |
| 7.0 | 840 | #9812, #10181 | This has been deprecated and off by default since Redis 6 and is no longer |
| 7.0 | 843 | #9812 | * SCRIPT LOAD and SCRIPT FLUSH are no longer propagated to replicas / AOF (#9812) |
| 7.0 | 868 | #9034 | default is in use (#9034) |
| 7.0 | 870 | #10092 | * Config: repl-diskless-sync is now set to yes by default (#10092) |
| 7.0 | 945 | #9872 | * shutdown-timeout, default 10 seconds (#9872) |
| 7.0 | 951 | #9462 | * latency-tracking, enabled by default, and latency-tracking-info-percentiles (#9462) |
| 7.2 | 593 | #11713 | * WAIT now no longer waits for the replication offset after your last command, |