#!/usr/bin/env python3
"""Integrate RE-ARC into our Qwen-SFT training mix (REAL, not a scaffold).

RE-ARC (github.com/michaelhodel/re-arc) is 400 procedural generators that mirror
the ARC-1 training-task distribution and sample infinitely. It was the sole
pretraining corpus behind the ARChitects' 71.6% public-eval result and is part
of the synthetic mix NVARC-style approaches pretrain on. We convert its output
into the EXACT pool-row schema the Qwen trainer streams, so RE-ARC tasks train
alongside our own per-puzzle generators.

Pipeline (one source of truth for rendering — reuse the SFT builder):
  1. import re-arc generators+verifiers (stub matplotlib: utils.py only needs it
     for plotting, which the generators never call).
  2. per task key: sample n VERIFIED instances (verifier(input)==output,
     non-degenerate, deduped on input) -> a bank of {input,output} pairs.
  3. group into episodes (n_demos demos + n_query queries, all same key/rule),
     render via scripts.build_qwen_sft_dataset.fmt_episode / episode_messages.
  4. emit {text, messages, task_id, demo_count, query_count} JSONL shards, with
     task_id = "rearc_<key>" so they're distinguishable in the pool.
  5. if difficulty weights are provided, use them for BOTH which keys are selected
     (when task_limit < all keys) and how many episodes each selected key receives.

Usage:
  python3 scripts/integrate_re_arc.py --re-arc-path ~/re-arc \
      --episodes-per-task 8 --n-demos-min 3 --n-demos-max 6 \
      --n-query-min 1 --n-query-max 3 --out-dir data/generated/re_arc --seed 0

Kaggle note: bundle the generated shards as a Dataset (no internet in GPU kernels).
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import random
import sys
import types
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# reuse the SFT builder's renderer so RE-ARC rows are byte-identical in shape to
# our own pool rows (NVARC serialization lives in ONE place).
from scripts.build_qwen_sft_dataset import fmt_episode, episode_messages
from scripts.difficulty_sampling import load_weights, weighted_order, scaled_episodes


def _stub_matplotlib():
    """re-arc/utils.py imports matplotlib at module load (only for plotting).
    Stub it so generators import on boxes with a broken/absent matplotlib."""
    mpl = types.ModuleType("matplotlib"); mpl.__path__ = []
    pyplot = types.ModuleType("matplotlib.pyplot")
    colors = types.ModuleType("matplotlib.colors")
    colors.ListedColormap = lambda *a, **k: None
    colors.Normalize = lambda *a, **k: None
    for fn in ("imshow", "show", "figure", "subplots", "savefig", "close", "axis", "title"):
        setattr(pyplot, fn, lambda *a, **k: None)
    mpl.pyplot = pyplot; mpl.colors = colors
    sys.modules.update({"matplotlib": mpl, "matplotlib.pyplot": pyplot,
                        "matplotlib.colors": colors})


def load_re_arc(re_arc_path):
    p = Path(re_arc_path).expanduser()
    if not p.exists():
        sys.exit(f"re-arc not found at {p}. Clone: "
                 f"git clone https://github.com/michaelhodel/re-arc {p}")
    _stub_matplotlib()
    sys.path.insert(0, str(p))
    import generators as G
    import verifiers as V
    gens = {k.split("generate_")[1]: getattr(G, k)
            for k in dir(G) if k.startswith("generate_")}
    vers = {k.split("verify_")[1]: getattr(V, k)
            for k in dir(V) if k.startswith("verify_")}
    return gens, vers




def stable_rearc_version(key: str, gen, ver) -> str:
    """Stable provenance fingerprint for a RE-ARC generator/verifier pair.

    Never use ``str(function)`` here: it embeds a process-local memory address
    (``<function verify_x at 0x...>``), so two identical runs produce different
    "versions" and stale-shard audits cannot compare rows.  Hash the actual
    source text instead; if inspect fails for a packaged function, fall back to
    module + qualname so the value is still address-free and deterministic.
    """
    parts = []
    for fn in (gen, ver):
        try:
            parts.append(inspect.getsource(fn))
        except (OSError, TypeError):
            parts.append(f"{getattr(fn, '__module__', '')}:{getattr(fn, '__qualname__', repr(fn))}")
    digest = hashlib.sha256("\n---\n".join(parts).encode()).hexdigest()[:16]
    return f"rearc:{key}:{digest}"


def _as_lists(grid):
    return [[int(v) for v in row] for row in grid]


def sample_bank(gen, ver, n, rng, *, diff_lb=0.0, diff_ub=1.0, max_tries=None):
    """n VERIFIED, deduped, non-degenerate {input,output} pairs for one key."""
    bank, seen = [], set()
    tries = 0
    cap = max_tries or n * 25
    while len(bank) < n and tries < cap:
        tries += 1
        try:
            ex = gen(diff_lb, diff_ub)
            inp, out = ex["input"], ex["output"]
            if not inp or not out:
                continue
            if ver(inp) != out:                      # rule self-consistency
                continue
            if inp == out:                           # skip identity (degenerate)
                continue
            key = (tuple(map(tuple, inp)), tuple(map(tuple, out)))
            if key in seen:
                continue
            seen.add(key)
            bank.append({"input": _as_lists(inp), "output": _as_lists(out)})
        except Exception:
            continue
    return bank


def convert(re_arc_path, out_dir, *, episodes_per_task, n_demos_min, n_demos_max,
            n_query_min, n_query_max, seed, shard_rows, task_limit, shuffle_tasks,
            weights=None):
    gens, vers = load_re_arc(re_arc_path)
    keys = sorted(k for k in gens if k in vers)
    rng = random.Random(seed)
    if weights:
        # Bias the minted subset toward keys the model is currently bad at
        # (looked up by the SAME task_id the rows carry: "rearc_<key>").
        # In the hourly cron, task_limit is often the full RE-ARC universe, so
        # weighted_order alone is only a permutation. scaled_episodes below is
        # what makes adaptivity active in that common case.
        keys = weighted_order(keys, weights, seed, key=lambda k: f"rearc_{k}")
    elif shuffle_tasks:
        rng.shuffle(keys)
    if task_limit:
        keys = keys[:task_limit]

    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    rows, shard_i, written, skipped = [], 0, 0, 0

    def flush(buf):
        nonlocal shard_i
        path = out_dir / f"shard_{shard_i:03d}.jsonl"
        # atomic publish: write a temp then rename, so the live trainer never
        # globs (and permanently consumes) a half-written shard.
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w") as f:
            for r in buf:
                f.write(json.dumps(r) + "\n")
        tmp.replace(path)
        shard_i += 1
        return path

    for ti, key in enumerate(keys):
        # enough verified instances to draw `episodes_per_task` varied episodes
        need = max(n_demos_max + n_query_max, 12)
        bank = sample_bank(gens[key], vers[key], need, rng)
        if len(bank) < n_demos_min + n_query_min:
            skipped += 1
            continue
        task_id = f"rearc_{key}"
        n_ep = scaled_episodes(episodes_per_task, task_id, weights, seed=seed)
        for ep in range(n_ep):
            nd = rng.randint(n_demos_min, n_demos_max)
            nq = rng.randint(n_query_min, n_query_max)
            if nd + nq > len(bank):
                nd = max(n_demos_min, min(nd, len(bank) - n_query_min))
                nq = max(n_query_min, min(nq, len(bank) - nd))
            pick = rng.sample(bank, nd + nq)
            demos, queries = pick[:nd], pick[nd:nd + nq]
            rows.append({
                "text": fmt_episode(demos, queries),
                "messages": episode_messages(demos, queries),
                "task_id": task_id,
                "demo_count": len(demos), "query_count": len(queries),
                "source_stream": "rearc",
                "source_key": key,
                "source_seed": seed,
                "episode_index": ep,
                "generator_version": stable_rearc_version(key, gens[key], vers[key]),
            })
            written += 1
            if len(rows) >= shard_rows:
                p = flush(rows); print(f"wrote {p} ({len(rows)} rows)"); rows = []
        if (ti + 1) % 50 == 0:
            print(f"  {ti+1}/{len(keys)} keys, {written} rows, {skipped} skipped", file=sys.stderr)

    if rows:
        p = flush(rows); print(f"wrote {p} ({len(rows)} rows)")
    print(f"DONE: {written} rows across {shard_i} shards from {len(keys)-skipped}/{len(keys)} keys "
          f"({skipped} keys skipped for too-few verified instances) -> {out_dir}")
    return written


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--re-arc-path", default="~/re-arc")
    ap.add_argument("--out-dir", default=str(REPO / "data/generated/re_arc"))
    ap.add_argument("--episodes-per-task", type=int, default=8)
    ap.add_argument("--n-demos-min", type=int, default=3)
    ap.add_argument("--n-demos-max", type=int, default=6)
    ap.add_argument("--n-query-min", type=int, default=1)
    ap.add_argument("--n-query-max", type=int, default=3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--shard-rows", type=int, default=5000)
    ap.add_argument("--task-limit", type=int, default=0)
    ap.add_argument("--shuffle-tasks", action="store_true")
    ap.add_argument("--difficulty-weights", default=None,
                    help="JSON {task_id: weight}. Biases the --task-limit subset toward "
                         "high-loss re-arc keys and scales episodes/key "
                         "(looked up as 'rearc_<key>').")
    return ap.parse_args()


def main() -> int:
    a = parse_args()
    written = convert(a.re_arc_path, a.out_dir, episodes_per_task=a.episodes_per_task,
                      n_demos_min=a.n_demos_min, n_demos_max=a.n_demos_max,
                      n_query_min=a.n_query_min, n_query_max=a.n_query_max, seed=a.seed,
                      shard_rows=a.shard_rows, task_limit=a.task_limit,
                      shuffle_tasks=a.shuffle_tasks,
                      weights=load_weights(a.difficulty_weights))
    if written <= 0:
        print("ERROR: RE-ARC integration wrote 0 rows", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
