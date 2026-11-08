"""Compose generic primitives into novel, contest-scaled task concepts — SCAFFOLD.

generate_pair(seed, ...) -> {input, output, program, chain, meta}
  * builds a dense random INPUT scaled to the contest distribution
    (default ~15-25 cells/side, ~25-30 components — closes the density gap
    our dashboard shows: our corpus ~8 comp4 vs eval ~30), then
  * applies a random chain of 1-3 IMPLEMENTED primitives to derive the OUTPUT,
  * returns the equivalent Racket `program` (pipe of the per-primitive heads).

Uses GenCtx (the same keyed-draw discipline as per_puzzle generators); NO
`import random` — randomness comes from ctx.draw_rng.

emit_shard writes N pairs to a JSONL shard for the SFT / episode pipeline.
"""
from __future__ import annotations

import json
from pathlib import Path

from puzzle_generators.base import gen_ctx
from puzzle_generators.generic.primitives import IMPLEMENTED, REGISTRY


def _build_dense_input(ctx, rng, *, difficulty):
    """A contest-scaled dense scatter (C1/C2: large grid, many components)."""
    if difficulty == "easy":
        h, w, ncols, density = rng.randint(8, 12), rng.randint(8, 12), rng.randint(2, 4), 0.18
    elif difficulty == "hard":
        h, w, ncols, density = rng.randint(20, 28), rng.randint(20, 28), rng.randint(5, 8), 0.30
    else:
        h, w, ncols, density = rng.randint(14, 20), rng.randint(14, 20), rng.randint(4, 6), 0.24
    palette = rng.sample(range(1, 10), ncols)
    g = [[0] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if rng.random() < density:
                g[r][c] = rng.choice(palette)
    return g


def generate_pair(seed, sample_index=0, *, difficulty="medium", n_primitives=None,
                  **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version="0.1.0",
                  task_id="generic_compose", difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("compose")
    g = _build_dense_input(ctx, rng, difficulty=difficulty)

    k = n_primitives or ctx.draw_int("n_primitives", 1, 3)
    chain = [rng.choice(IMPLEMENTED) for _ in range(k)]
    out = g
    heads = []
    for prim in chain:
        p = prim.sample(rng, out)
        out = prim.apply(out, p, rng)
        heads.append(prim.racket(p))

    # Racket program = left-to-right pipe of the primitive heads. Each head is
    # written as a 1-arg form on `g`; pipe threads the grid through them.
    program = "(rule! (pipe " + " ".join(f"(lambda (g) {h})" for h in heads) + "))" \
        if len(heads) > 1 else f"(rule! (lambda (g) {heads[0]}))"
    return {
        "input": g,
        "output": out,
        "program": program,
        "chain": [prim.name for prim in chain],
        "meta": {"difficulty": difficulty, "n_primitives": k},
    }


def emit_shard(out_path, n=1000, *, seed0=0, difficulty="medium"):
    """Write N (input, output, program) pairs to a JSONL shard.

    NOTE: a TASK in ARC is a few demo pairs that share ONE rule. To make tasks
    (not loose pairs), group several pairs that share the same chain+params.
    TODO: add a `group_size` mode that fixes the chain and resamples only the
    input, emitting {train:[...], test:[...]} task rows for the episode dataset.
    """
    out_path = Path(out_path); out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        for i in range(n):
            f.write(json.dumps(generate_pair(seed0 + i, 0, difficulty=difficulty)) + "\n")
    return out_path


if __name__ == "__main__":
    # smoke: print one pair per difficulty
    for d in ("easy", "medium", "hard"):
        r = generate_pair(0, 0, difficulty=d)
        print(d, "chain=", r["chain"], "in=", len(r["input"]), "x", len(r["input"][0]),
              "program=", r["program"][:80])
