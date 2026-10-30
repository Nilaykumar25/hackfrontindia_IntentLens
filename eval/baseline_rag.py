"""Vector-only baseline: top-k comments by similarity -> LLM answer. No graph, no supersession, no refusal logic."""
from backend.app.graph.db import Neo4jDB
from backend.app.llm.provider import LLM, embed
from backend.app.retrieval import cypher as Q

SYSTEM = "Answer the question about why the code is the way it is, using the provided excerpts. Answer concisely."


def baseline_answer(db: Neo4jDB, llm: LLM, question: str, k: int = 5) -> dict:
    hits = db.run(Q.RELATED_DISCUSSIONS, k=k, embedding=embed([question])[0])
    ctx = "\n\n".join(f"[{h['id']}] {h['snippet']}" for h in hits)
    return {"status": "answered", "answer": llm.complete(SYSTEM, f"Question: {question}\n\nExcerpts:\n{ctx}", 500),
            "cited_ids": [h["id"] for h in hits], "superseded_notice": None, "confidence": None}
