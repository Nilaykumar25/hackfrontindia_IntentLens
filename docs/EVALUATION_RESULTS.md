# Evaluation Results

## Calibration Check

- Mean confidence (correct answers): **0.474**
- Mean confidence (incorrect answers): **0.091**
- Gap: **0.383**

If the gap is negative or near zero, the confidence model is not discriminative.

## Dev Split (Keyword)

| Metric | Vector-RAG baseline | IntentLens |
|---|---|---|
| answer_accuracy | 0.8 | 0.75 |
| supersession_accuracy | 0.0 | 0.333 |
| refusal_correctness | 0.0 | 1.0 |
| citation_precision | None | None |
| mean_conf_when_right | None | 0.474 |
| mean_conf_when_wrong | None | 0.091 |
| p95_latency_ms | 1869 | 2060 |

## Held-Out Split (Keyword)

| Metric | Vector-RAG baseline | IntentLens |
|---|---|---|
| answer_accuracy | 1.0 | 0.2 |
| supersession_accuracy | 0.5 | 0.5 |
| refusal_correctness | 0.0 | 1.0 |
| citation_precision | None | None |
| mean_conf_when_right | None | 0.218 |
| mean_conf_when_wrong | None | 0.079 |
| p95_latency_ms | 2143 | 2122 |

## Per-Item Results (Dev Split)

| ID | Type | IntentLens | Baseline | Confidence | Latency (ms) |
|---|---|---|---|---|---|
| A01 | answerable | ✓ | ✓ | 0.467 | 26922 |
| A02 | answerable | ✓ | ✗ | 0.799 | 372 |
| A03 | answerable | ✗ | ✓ | 0.317 | 1823 |
| A04 | answerable | ✓ | ✓ | 0.773 | 1557 |
| A05 | answerable | ✓ | ✓ | 0.813 | 2060 |
| A06 | answerable | ✓ | ✓ | 0.816 | 1537 |
| A07 | answerable | ✓ | ✓ | 0.847 | 1689 |
| A08 | answerable | ✓ | ✗ | 0.626 | 1488 |
| A09 | answerable | ✓ | ✗ | 0.5 | 1617 |
| A10 | answerable | ✓ | ✓ | 0.545 | 1384 |
| A11 | answerable | ✓ | ✓ | 0.35 | 1287 |
| A12 | answerable | ✗ | ✓ | 0.0 | 596 |
| A13 | answerable | ✓ | ✓ | 0.62 | 1930 |
| A14 | answerable | ✓ | ✓ | 0.65 | 1814 |
| A15 | answerable | ✓ | ✓ | 0.35 | 1609 |
| A16 | answerable | ✓ | ✓ | 0.677 | 1902 |
| A17 | answerable | ✗ | ✓ | 0.0 | 574 |
| A18 | answerable | ✓ | ✗ | 0.424 | 1555 |
| A19 | answerable | ✗ | ✓ | 0.0 | 568 |
| A20 | answerable | ✗ | ✓ | 0.0 | 625 |
| U01 | unanswerable | ✓ | ✗ | 0.0 | 557 |
| U02 | unanswerable | ✓ | ✗ | 0.0 | 391 |
| U03 | unanswerable | ✓ | ✗ | 0.0 | 650 |
| U04 | unanswerable | ✓ | ✗ | 0.0 | 547 |
| U05 | unanswerable | ✓ | ✗ | 0.0 | 545 |
| S01 | supersession | ✓ | ✗ | 0.688 | 1638 |
| S02 | supersession | ✗ | ✗ | 0.317 | 2453 |
| S03 | supersession | ✗ | ✗ | 0.0 | 576 |
