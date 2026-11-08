#!/usr/bin/env python3
"""SYNTHETIC-PIPE exec-trace generator — the execution-guided grounding (#3) adapted to our corpus.

Our real programs are monolithic let-lambdas with no pipe/grid-intermediate structure, so we can't
trace them. Instead we SYNTHESIZE composable programs: pick a random chain of grid->grid primitives
(geometric + recolor/gravity/remove-color), nest them, and execute each PREFIX on a random input grid
through the Racket bridge. Each prefix + input -> its intermediate grid becomes an `<exec>` row. This
teaches step-by-step execution semantics (what each primitive DOES on a real grid), which is what
execution-guided generation needs at inference. Reuses the `<exec>` task (no new vocab).

Pure synthetic data (no canonical dependency). Robust: any exec-fail truncates that chain, counted.

  python3 scripts/gen_synthpipe_data.py --pool data/coder_dsl/stream_pool --shard-size 1500
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
from dsl_v2 import build_core_vocab, to_tokens, grid_to_tokens  # noqa: E402

_RNG = random.Random(20260701)


def _rand_grid(rng):
    h, w = rng.randint(3, 14), rng.randint(3, 14)
    palette = rng.sample(range(1, 10), rng.randint(1, 4))
    return [[(rng.choice(palette) if rng.random() < 0.35 else 0) for _ in range(w)] for _ in range(h)]


def _transforms(rng):
    """Composable grid->grid stages as inner-expr wrappers. Geometric ones are param-free; the rest
    sample fixed params per chain so the chain is deterministic."""
    def geom(name):
        return lambda inner: f"({name} {inner})"
    ts = [("flip-lr", geom("flip-lr")), ("flip-ud", geom("flip-ud")), ("transpose", geom("transpose")),
          ("rotate-cw", geom("rotate-cw")), ("rotate-ccw", geom("rotate-ccw")),
          ("rotate-180", geom("rotate-180"))]
    a, b = rng.sample(range(0, 10), 2)
    ts.append(("recolor", lambda inner, a=a, b=b: f"(recolor {inner} {a} {b})"))
    d = rng.choice(["up", "down", "left", "right"])
    ts.append(("gravity", lambda inner, d=d: f'(gravity {inner} "{d}")'))
    c = rng.randint(1, 9)
    ts.append(("remove-color", lambda inner, c=c: f"(remove-color {inner} {c})"))
    return ts


def _valid(g):
    return (isinstance(g, list) and g and all(isinstance(r, list) and r for r in g)
            and len({len(r) for r in g}) == 1 and all(isinstance(c, int) and 0 <= c <= 9 for r in g for c in r))


def synthpipe_rows(core, ver, rng, n_stages):
    """One random chain of n_stages transforms; emit an <exec> row per PREFIX (prefix + input ->
    intermediate grid). Returns (rows, n_execs)."""
    grid = _rand_grid(rng)
    ts = _transforms(rng)
    rows, inner, done = [], "g", 0
    for _ in range(n_stages):
        _, wrap = rng.choice(ts)
        inner = wrap(inner)
        prog = f"(rule! {inner})"
        try:
            out = ver.apply(prog, grid)
        except Exception:
            break
        if not _valid(out):
            break
        try:
            ptoks = to_tokens(prog, core)
        except Exception:
            break
        rows.append({"task_id": "synthpipe", "task_type": "<exec>", "synthpipe": True,
                     "input_tokens": ["<exec>"] + ptoks + ["<io>"] + grid_to_tokens(grid),
                     "program_tokens": grid_to_tokens(out)})
        done += 1
    return rows, done



def _next_shard_n(pool, prefix):
    """Collision-proof shard numbering: continue after the max existing index
    across the pool AND consumed/ (a fresh launch used to restart at 0 and
    silently OVERWRITE unconsumed shards)."""
    import re
    mx = -1
    for d in (pool, pool / "consumed"):
        if d.is_dir():
            for f in d.glob(prefix + "*.jsonl"):
                m = re.search(r"(\d+)\.jsonl$", f.name)
                if m:
                    mx = max(mx, int(m.group(1)))
    return mx + 1

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", default=str(ROOT / "data/coder_dsl/stream_pool"))
    ap.add_argument("--shard-size", type=int, default=1500)
    ap.add_argument("--min-stages", type=int, default=2)
    ap.add_argument("--max-stages", type=int, default=5)
    ap.add_argument("--max-pool-shards", type=int, default=40)
    ap.add_argument("--max-shards", type=int, default=0)
    a = ap.parse_args()
    from coder_synth_verify import ProgramVerifier
    ver = ProgramVerifier()
    _toks, core = build_core_vocab(0)
    pool = Path(a.pool); pool.mkdir(parents=True, exist_ok=True)
    print(f"SYNTH-PIPE exec-trace -> {pool} | stages {a.min_stages}-{a.max_stages}", flush=True)
    buf, shard_n, made, execs = [], _next_shard_n(pool, "shard_s"), 0, 0
    while True:
        if a.max_pool_shards and len(list(pool.glob("shard_s*.jsonl"))) >= a.max_pool_shards:
            time.sleep(5); continue
        r, d = synthpipe_rows(core, ver, _RNG, _RNG.randint(a.min_stages, a.max_stages))
        buf += r; execs += d
        while len(buf) >= a.shard_size:
            shard = pool / f"shard_s{shard_n:06d}.jsonl"; tmp = shard.with_suffix(".tmp")
            with tmp.open("w") as f:
                for row in buf[:a.shard_size]:
                    f.write(json.dumps(row) + "\n")
            tmp.rename(shard)                 # shard_* so the trainer consumes it
            buf = buf[a.shard_size:]; shard_n += 1; made += 1
            print(f"wrote synthpipe shard {made} (prefix-execs={execs})", flush=True)
            if a.max_shards and made >= a.max_shards:
                return 0


if __name__ == "__main__":
    raise SystemExit(main())
