"""Metric helpers with keyword matching and optional LLM judge for borderline cases.

Reports both keyword-based and LLM-judged numbers when the judge is available.
"""
from __future__ import annotations

import logging

log = logging.getLogger(__name__)

_judge_system = """You judge whether a given answer correctly addresses a question about Redis engineering decisions.
Return JSON: {"correct": true/false, "reason": "one sentence"}.
Rules:
- "correct" means the answer addresses the specific question and contains accurate information from the decision.
- An answer that refuses or says "no decision found" is correct for unanswerable questions.
- An answer that makes up facts not in the evidence is incorrect."""


def keyword_hit(text: str, keywords: list[str], min_frac: float = 0.5) -> bool:
    if not keywords:
        return False
    t = (text or "").lower()
    return sum(k.lower() in t for k in keywords) / len(keywords) >= min_frac


def llm_judge(question: str, answer: str, expected_keywords: list[str], llm=None) -> bool | None:
    """Use an LLM to judge borderline keyword matches. Returns True/False or None if judge unavailable."""
    if llm is None:
        return None
    try:
        user = (
            f"QUESTION: {question}\n\n"
            f"ANSWER: {answer[:500]}\n\n"
            f"EXPECTED TOPICS: {', '.join(expected_keywords)}\n\n"
            f"Is the answer correct?"
        )
        result = llm.complete_json(_judge_system, user, 200)
        return bool(result.get("correct", False))
    except Exception as exc:
        log.warning("LLM judge error: %s", exc)
        return None


def score_item(item: dict, resp: dict, llm=None) -> dict:
    refused = resp.get("status") == "refused"
    out = {"id": item["id"], "type": item["type"]}

    if item["type"] == "unanswerable":
        out["correct"] = refused
        out["llm_correct"] = refused  # LLM judge trivially agrees for unanswerable
    else:
        # Keyword matching
        kw_ok = (not refused) and keyword_hit(resp.get("answer", ""), item.get("expected_keywords", []))
        if item["type"] == "supersession":
            stale = keyword_hit(resp.get("answer", ""), item.get("superseded_keywords", []), 0.5)
            kw_ok = kw_ok and not stale and bool(resp.get("superseded_notice")) == item.get("expect_superseded_notice", True)
        out["correct"] = kw_ok

        # LLM judge (optional, for borderline cases)
        if llm is not None and not refused:
            out["llm_correct"] = llm_judge(item["question"], resp.get("answer", ""), item.get("expected_keywords", []), llm)
        else:
            out["llm_correct"] = kw_ok

        gold = set(item.get("gold_evidence_ids", []))
        cited = set(resp.get("cited_ids", []))
        out["citation_precision"] = (len(gold & cited) / len(cited)) if gold and cited else None

    out["confidence"] = (resp.get("confidence") or {}).get("score")
    out["latency_ms"] = resp.get("latency_ms")
    return out


def summarise(rows: list[dict], use_llm: bool = False) -> dict:
    """Summarise evaluation results. If use_llm=True, report LLM-judged numbers."""
    correct_key = "llm_correct" if use_llm else "correct"

    def rate(rs):
        vals = [r.get(correct_key, r.get("correct", False)) for r in rs]
        return round(sum(1 for v in vals if v) / len(vals), 3) if vals else None

    cp = [r["citation_precision"] for r in rows if r.get("citation_precision") is not None]
    right = [r["confidence"] for r in rows if r.get(correct_key, r.get("correct", False)) and r["confidence"] is not None]
    wrong = [r["confidence"] for r in rows if not r.get(correct_key, r.get("correct", False)) and r["confidence"] is not None]
    lat = sorted(r["latency_ms"] for r in rows if r.get("latency_ms"))
    return {
        "answer_accuracy": rate([r for r in rows if r["type"] == "answerable"]),
        "supersession_accuracy": rate([r for r in rows if r["type"] == "supersession"]),
        "refusal_correctness": rate([r for r in rows if r["type"] == "unanswerable"]),
        "citation_precision": round(sum(cp) / len(cp), 3) if cp else None,
        "mean_conf_when_right": round(sum(right) / len(right), 3) if right else None,
        "mean_conf_when_wrong": round(sum(wrong) / len(wrong), 3) if wrong else None,
        "p95_latency_ms": lat[int(0.95 * (len(lat) - 1))] if lat else None,
    }
