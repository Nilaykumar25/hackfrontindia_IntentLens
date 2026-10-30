/**
 * demoQuestions.js
 *
 * Verified demo questions for the suggestion buttons and ?demo=1 mode.
 * Every question was tested against the live API — states and confidences
 * are confirmed real results, not estimates.
 *
 * Expected states:
 *   ANSWERED   — decision found, confidence ≥ Low, answer + evidence returned
 *   SUPERSEDED — status=answered with superseded_notice set;
 *                older decision appears in history[] with status=SUPERSEDED
 *   REFUSED    — status="refused"; no governing decision in graph
 */

export const DEMO_QUESTIONS = [
  // ── 1. ANSWERED / High confidence ────────────────────────────────────────
  {
    id: "aof-mechanism",
    question: "What is the rationale for the Multi-Part AOF mechanism in Redis 7.0?",
    expectedState: "answered",
    supersededNoticeExpected: false,
    expectedConfidence: "High",
    entityHint: "appenddirname",
    description: "ANSWERED — High confidence with commit evidence",
    note:
      "Hits the Multi-Part AOF decision (PR #9788, 2022-01-04). " +
      "Returns High confidence with commit evidence.",
  },

  // ── 2. SUPERSEDED — bind address default changed ──────────────────────────
  {
    id: "bind-fail-default",
    question:
      "Why does Redis fail to start by default when a requested bind address is not available?",
    expectedState: "answered",
    supersededNoticeExpected: true,    // superseded_notice IS populated
    expectedConfidence: "High",
    entityHint: "config:bind",
    description: "SUPERSEDED — bind default changed; older decision in history",
    note:
      "The '-' prefix behaviour (ignore EADDRNOTAVAIL) was SUPERSEDED by " +
      "'Default behavior: fail to start if requested bind address is not available' (#7936). " +
      "Response includes superseded_notice and the SUPERSEDED older decision in history[]. " +
      "Confirmed: superseded_notice present, history[0].status='SUPERSEDED'.",
  },

  // ── 3. REFUSED — function with no governing decision ─────────────────────
  {
    id: "update-slaves-waiting",
    question:
      "What design decision explains why updateSlavesWaitingBgsave uses its current implementation strategy?",
    expectedState: "refused",
    supersededNoticeExpected: false,
    expectedConfidence: "No answer",
    entityHint: "fn:src/replication.c::updateSlavesWaitingBgsave",
    description: "REFUSED — 37 commits, no governing Decision in graph",
    note:
      "updateSlavesWaitingBgsave has 37 commits but no mined Decision. " +
      "Returns status='refused' with 8 related discussions and last changers " +
      "(Ozan Tezcan, Oran Agra). Confirmed live.",
  },

  // ── 4. ANSWERED / evidence from Document node ─────────────────────────────
  {
    id: "replication-backlog-trim",
    question:
      "Why does Redis trim the replication backlog only when a new block is added, " +
      "not on every write?",
    expectedState: "answered",
    supersededNoticeExpected: false,
    expectedConfidence: "Medium",
    entityHint: "fn:src/replication.c::incrementalTrimReplicationBacklog",
    description: "ANSWERED — sourced from a source-comment Document node",
    note:
      "Decision mined from the incrementalTrimReplicationBacklog C comment block. " +
      "Evidence rail shows a Document node, demonstrating doc-sourced evidence.",
  },

  // ── 5. OUT-OF-SCOPE REFUSAL — epoll vs select ────────────────────────────
  {
    id: "epoll-select",
    question: "Why does Redis use epoll instead of select on Linux?",
    expectedState: "refused",
    supersededNoticeExpected: false,
    expectedConfidence: "No answer",
    entityHint: null,
    description: "REFUSED (out of scope) — ae_epoll.c is outside loaded subsystem",
    note:
      "The epoll/select choice lives in src/ae_epoll.c which is outside the " +
      "loaded subsystem paths (replication.c / rdb.c / aof.c / redis.conf). " +
      "Demonstrates graceful out-of-scope refusal.",
  },
];

/** The three canonical demo questions for the ?demo=1 one-click buttons */
export const THREE_DEMO_QUESTIONS = [
  DEMO_QUESTIONS[0], // ANSWERED — Multi-Part AOF
  DEMO_QUESTIONS[1], // SUPERSEDED — bind default
  DEMO_QUESTIONS[2], // REFUSED — updateSlavesWaitingBgsave
];

/** All 5 suggestion buttons in the Ask workspace */
export const SUGGESTION_QUESTIONS = DEMO_QUESTIONS.map((d) => d.question);
