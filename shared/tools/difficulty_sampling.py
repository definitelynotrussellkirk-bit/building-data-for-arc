"""Shared difficulty-weighted sampling for ALL pool integrators (DRY).

The trainer logs per-task loss -> scripts/aggregate_difficulty.py turns it into
{task_id: weight}. Current weights prefer digit-only metrics and blend
percentile ranks as 0.6*avg_digit + 0.3*p95_digit + 0.1*bad_digit_frac
(with a legacy avg/tail fallback), so delimiter/EOS spikes and single-token
maxima no longer dominate the sampling contract. Every data source that feeds
the pool (per-puzzle, re-arc, concepts, pair-banks) uses THESE helpers so the
loss->weight->sampling contract is defined exactly ONCE:

  - weighted_order(): bias WHICH tasks get minted (sources with a --task-limit).
  - scaled_episodes(): bias HOW MANY episodes a task gets (sources with no limit).

Unseen task_ids (e.g. a freshly-added generator with no loss history yet) fall
back to the MEDIAN weight, so new sources aren't starved or over-served until the
trainer has actually seen them and a real signal exists.
"""
from __future__ import annotations

import json
import os
import random


def load_weights(path):
    """Read {task_id: weight} JSON. Missing/empty => None (uniform sampling, fine);
    MALFORMED => fail loud. Silently returning None on a truncated/corrupt file
    would disable loss-adaptivity with no alarm (a real production hazard)."""
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            w = json.load(f)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"malformed difficulty weights JSON at {path}: {e}") from e
    except OSError:
        return None
    if not isinstance(w, dict):
        raise RuntimeError(f"difficulty weights must be a JSON object, got {type(w).__name__}: {path}")
    return w or None


def _median(weights):
    vals = sorted(weights.values())
    return vals[len(vals) // 2] if vals else 1.0


def weighted_order(items, weights, seed, key=lambda x: x):
    """Efraimidis-Spirakis weighted sampling WITHOUT replacement: priority
    u**(1/w), sorted descending, so higher-weight (harder) items rank higher in
    expectation. `key(item)` -> the task_id string used for the weight lookup
    (lets callers weight raw rows/paths by the task_id they'll be tagged with).
    Unseen task_ids get the median weight. Returns items reordered."""
    if not weights:
        items = list(items)
        random.Random(seed).shuffle(items)
        return items
    rng = random.Random(seed)
    med = _median(weights)
    keyed = []
    for it in items:
        w = max(1e-6, float(weights.get(key(it), med)))
        u = rng.random() or 1e-12
        keyed.append((u ** (1.0 / w), it))
    keyed.sort(key=lambda p: p[0], reverse=True)
    return [it for _, it in keyed]


def scaled_episodes(base, task_id, weights, *, lo=0.5, hi=1.5, floor=0.15, seed=0):
    """Map a task's difficulty weight -> an episode count in [lo*base, hi*base].

    aggregate_difficulty.py writes weights in [floor, 1], so we normalize that
    interval BEFORE interpolating — otherwise an easy task at the floor maps to
    lo + (hi-lo)*floor (~0.65x), not lo*base. Now floor->lo, 1.0->hi. The
    fractional remainder is rounded STOCHASTICALLY (keyed by task_id+seed, so it's
    deterministic per run) so the expected count is exact. Unseen tasks -> median."""
    if not weights:
        return base
    med = _median(weights)
    w = float(weights.get(task_id, med))
    x = (w - floor) / max(1e-9, 1.0 - floor)             # normalize [floor,1] -> [0,1]
    x = max(0.0, min(1.0, x))
    raw = base * (lo + (hi - lo) * x)
    n = int(raw)
    frac = raw - n
    r = random.Random(f"{task_id}:{seed}").random()
    return max(1, n + (1 if r < frac else 0))
