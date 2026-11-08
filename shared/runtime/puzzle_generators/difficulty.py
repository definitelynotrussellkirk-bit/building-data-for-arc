"""Per-instance difficulty scoring and bucketing.

Phase 6 of docs/PUZZLE_GENERATOR_ROADMAP.md.

A puzzle instance is `{train: [{input, output}, ...], test: [...]}`. The
score is a deterministic weighted sum of three normalized features
extracted from the first train pair:

  - size:    log-scaled grid area (5x5 ≈ low, 30x30 ≈ high)
  - palette: number of distinct colors / 8 (max non-bg palette size)
  - delta:   magnitude of input→output dimension change

All in [0, 1]; weighted to a final score in [0, 1].

This is a heuristic — it doesn't know what the rule does. Phase 7 may
swap in something semantic (rule complexity, AST depth, primitives
used). For now the heuristic is enough for curriculum bucketing.
"""
from __future__ import annotations

import math
from typing import Iterable

# Bucket thresholds. Anything <= EASY_MAX is "easy"; (EASY_MAX, HARD_MIN]
# is "medium"; > HARD_MIN is "hard". These are *absolute* thresholds —
# useful for cross-corpus comparisons but often too strict for any one
# generator's natural range. Use `relative_buckets()` for a calibrated
# version that splits the actual distribution into terciles.
EASY_MAX = 0.34
HARD_MIN = 0.67


def relative_buckets(scores: list[float]) -> tuple[float, float]:
    """Return (easy_max, hard_min) thresholds at the 33rd and 67th
    percentiles of the given scores. Use this when bucketing a curriculum
    batch where the generator's natural range doesn't span 0..1."""
    if not scores:
        return EASY_MAX, HARD_MIN
    sorted_scores = sorted(scores)
    n = len(sorted_scores)
    # Floor/ceiling so buckets don't overlap when scores cluster tightly.
    e = sorted_scores[max(0, n // 3 - 1)]
    h = sorted_scores[min(n - 1, (2 * n) // 3)]
    if h <= e:
        h = e + 1e-6
    return e, h


def score(instance: dict) -> float:
    """Compute a difficulty score in [0, 1]. Higher = harder.

    Uses the first train pair as the canonical sample. If the instance
    has no train pairs, returns 0.5 (unknown)."""
    pairs = instance.get("train") or []
    if not pairs:
        return 0.5
    p = pairs[0]
    inp = p.get("input"); out = p.get("output")
    if not inp or not isinstance(inp, list) or not isinstance(inp[0], list):
        return 0.5

    h_in = len(inp); w_in = len(inp[0])
    if h_in == 0 or w_in == 0:
        return 0.5
    if not out or not isinstance(out, list) or not isinstance(out[0], list):
        h_out, w_out = h_in, w_in
    else:
        h_out = len(out); w_out = len(out[0])

    # 1. Size — log-scaled relative to a 30x30 = 900 ceiling
    area = h_in * w_in
    size_factor = min(1.0, math.log(max(area, 2)) / math.log(900))

    # 2. Palette — distinct colors in the input, capped at 8 (typical max)
    colors = {v for row in inp for v in row}
    palette_factor = min(1.0, len(colors) / 8.0)

    # 3. Dim-change magnitude
    if h_out > 0 and w_out > 0:
        ratios = (
            h_out / h_in, h_in / h_out,
            w_out / w_in, w_in / w_out,
        )
        max_change = max(ratios) - 1.0
    else:
        max_change = 0.0
    delta_factor = min(1.0, max_change / 4.0)

    return max(0.0, min(1.0,
        0.40 * size_factor + 0.30 * palette_factor + 0.30 * delta_factor))


def bucket(s: float, *, easy_max: float = EASY_MAX, hard_min: float = HARD_MIN) -> str:
    """Map a score to one of {'easy', 'medium', 'hard'}.
    Optional thresholds let callers use relative_buckets() for tighter,
    distribution-calibrated bucketing."""
    if s <= easy_max: return "easy"
    if s >= hard_min: return "hard"
    return "medium"


def score_batch(batch: Iterable[dict]) -> list[tuple[dict, float]]:
    """Score every instance in a batch; return (instance, score) pairs."""
    return [(inst, score(inst)) for inst in batch]


def histogram(scored: list[tuple[dict, float]],
              *, easy_max: float = EASY_MAX, hard_min: float = HARD_MIN
              ) -> dict[str, int]:
    """Bucket counts {'easy': N, 'medium': N, 'hard': N}."""
    counts = {"easy": 0, "medium": 0, "hard": 0}
    for _, s in scored:
        counts[bucket(s, easy_max=easy_max, hard_min=hard_min)] += 1
    return counts
