# 5 Example Questions — Verification Results

## Why was repl-diskless-sync changed to yes by default?
**Status:** ANSWERED
**Entity hint:** `config:repl-diskless-sync`
**Result:** repl-diskless-sync was changed to yes by default to align with redis being built with repl compression disabled by default. [E1] The change involved commenting out repl-compression related configs in 
**Superseded notice:** This decision replaced: “Add zstd compression for replication with IO-threads only” (2026-06-24).

## Why does Redis use PEXPIREAT instead of EXPIRE when replicating TTLs?
**Status:** ANSWERED
**Entity hint:** `src/replication.c`
**Result:** Redis introduced GETEX, GETDEL, and absolute-timestamp TTL options (EXAT, PXAT) to provide more flexible TTL replication capabilities. [E1] The commit specifically adds absolute-timestamp variants (EX

## Why does the replication backlog need to be trimmed?
**Status:** ANSWERED
**Entity hint:** `fn:src/replication.c::incrementalTrimReplicationBacklog`
**Result:** The replication backlog needs to be trimmed to prevent unbounded memory growth and ensure predictable performance. [E1] The commit title explicitly mentions verifying TLS server identity by default in

## Why does WAIT no longer wait for the offset after the last command?
**Status:** REFUSED
**Entity hint:** `fn:src/replication.c::waitCommand`
**Result:** No decision in the graph governs the entities named in this question.

## Why does AOF rewrite use a hard link instead of copying the file?
**Status:** ANSWERED
**Entity hint:** `fn:src/aof.c::aofInstallPreloadFile`
**Result:** AOF rewrite uses a hard link instead of copying the file to efficiently create a new AOF snapshot by reusing the existing base RDB file without duplicating its data. [E1] The base RDB file is stored a
