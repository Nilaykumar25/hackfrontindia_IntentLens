"""Run IntentLens and the vector-RAG baseline on the gold set.

Outputs docs/EVALUATION_RESULTS.md with both keyword and LLM-judged numbers,
split into dev and held-out sets.

Usage:
    python -m scripts.run_eval          # keyword matching only
    python -m scripts.run_eval --llm    # also use LLM judge
"""
import argparse
import json
import time

from backend.app.graph.db import get_db
from backend.app.llm.provider import get_llm
from backend.app.retrieval.graphrag import GraphRAG
from eval.baseline_rag import baseline_answer
from eval.metrics import score_item, summarise


def _load_gold():
    data = json.load(open("eval/gold_questions.json", encoding="utf-8"))
    items = data["questions"]
    splits = data.get("_splits", {})
    dev_ids = set(splits.get("dev", []))
    held_out_ids = set(splits.get("held_out", []))
    dev = [it for it in items if it["id"] in dev_ids]
    held = [it for it in items if it["id"] in held_out_ids]
    all_items = dev + held
    return all_items, dev, held


def _run_items(items, rag, db, llm, use_llm=False):
    a_rows, b_rows = [], []
    for it in items:
        # IntentLens
        r = rag.answer(it["question"]).model_dump()
        r["cited_ids"] = [e["id"] for e in r["evidence"]]
        a_rows.append(score_item(it, r, llm=llm if use_llm else None))

        # Baseline
        t0 = time.time()
        b = baseline_answer(db, llm, it["question"])
        b["latency_ms"] = int((time.time() - t0) * 1000)
        b_rows.append(score_item(it, b))

    return a_rows, b_rows


def _md_table(title, sa, sb, use_llm=False):
    metric_label = "LLM-judged" if use_llm else "Keyword"
    lines = [f"## {title} ({metric_label})", "",
             "| Metric | Vector-RAG baseline | IntentLens |", "|---|---|---|"]
    for k in sa:
        lines.append(f"| {k} | {sb.get(k)} | {sa[k]} |")
    lines.append("")
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm", action="store_true", help="Also run LLM judge")
    args = ap.parse_args()

    all_items, dev_items, held_items = _load_gold()
    db, llm = get_db(), get_llm()
    rag = GraphRAG(db, llm)

    print(f"Gold set: {len(all_items)} total ({len(dev_items)} dev, {len(held_items)} held-out)")

    # Run dev split
    print(f"Running dev split ({len(dev_items)} questions)...")
    dev_a, dev_b = _run_items(dev_items, rag, db, llm, use_llm=args.llm)

    # Run held-out split
    print(f"Running held-out split ({len(held_items)} questions)...")
    held_a, held_b = _run_items(held_items, rag, db, llm, use_llm=args.llm)

    # Summarise
    dev_sa = summarise(dev_a)
    dev_sb = summarise(dev_b)
    held_sa = summarise(held_a)
    held_sb = summarise(held_b)

    # Calibration check
    dev_correct_conf = [r["confidence"] for r in dev_a if r.get("correct") and r["confidence"] is not None]
    dev_wrong_conf = [r["confidence"] for r in dev_a if not r.get("correct") and r["confidence"] is not None]
    mean_right = round(sum(dev_correct_conf) / len(dev_correct_conf), 3) if dev_correct_conf else None
    mean_wrong = round(sum(dev_wrong_conf) / len(dev_wrong_conf), 3) if dev_wrong_conf else None

    # Build markdown
    lines = ["# Evaluation Results", "",
             "## Calibration Check", "",
             f"- Mean confidence (correct answers): **{mean_right}**",
             f"- Mean confidence (incorrect answers): **{mean_wrong}**",
             f"- Gap: **{round((mean_right or 0) - (mean_wrong or 0), 3)}**",
             "", "If the gap is negative or near zero, the confidence model is not discriminative.",
             ""]

    lines += _md_table("Dev Split", dev_sa, dev_sb)
    lines += _md_table("Held-Out Split", held_sa, held_sb)

    # LLM-judged results (if requested)
    if args.llm:
        dev_sa_llm = summarise(dev_a, use_llm=True)
        dev_sb_llm = summarise(dev_b, use_llm=True)
        lines += _md_table("Dev Split (LLM Judge)", dev_sa_llm, dev_sb_llm, use_llm=True)
        lines += _md_table("Held-Out Split (LLM Judge)", summarise(held_a, use_llm=True), summarise(held_b, use_llm=True), use_llm=True)

    # Per-item details
    lines += ["## Per-Item Results (Dev Split)", "",
              "| ID | Type | IntentLens | Baseline | Confidence | Latency (ms) |", "|---|---|---|---|---|---|"]
    for a, b in zip(dev_a, dev_b):
        lines.append(f"| {a['id']} | {a['type']} | {'✓' if a.get('correct') else '✗'} | {'✓' if b.get('correct') else '✗'} | {a.get('confidence')} | {a.get('latency_ms')} |")

    content = "\n".join(lines) + "\n"
    open("docs/EVALUATION_RESULTS.md", "w", encoding="utf-8").write(content)
    print("\n" + content)


if __name__ == "__main__":
    main()
