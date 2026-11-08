"""gen2: DOWNSCALE by an integer factor (ratios 2..5). The input is a
block-uniform field (each factor x factor block a single color); the rule
collapses each block to one cell. Program: (downscale g F). This is the
"downsize" task — big blocky input -> small output."""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.generic.concepts.resize import parity_check

VERSION = "1.0.0"
TASK_ID = "generic_resize_downscale"


def _factor_for(ctx, difficulty):
    if difficulty == "easy":
        return ctx.draw_int("factor", 2, 3)
    if difficulty == "hard":
        return ctx.draw_int("factor", 4, 5)
    return ctx.draw_int("factor", 2, 4)


def _upscale(g, f):
    out = []
    for row in g:
        big = []
        for v in row:
            big.extend([v] * f)
        for _ in range(f):
            out.append(big[:])
    return out


def _downscale(g, f):
    # take the top-left cell of each fxf block (matches prelude downscale default)
    return [[g[r * f][c * f] for c in range(len(g[0]) // f)]
            for r in range(len(g) // f)]


def _build_small(ctx, idx, colors, s):
    rng = ctx.draw_rng(f"small_{idx}")
    g = [[(rng.choice(colors) if rng.random() < 0.6 else 0) for _ in range(s)]
         for _ in range(s)]
    if len({v for row in g for v in row} - {0}) < 2:
        g[0][0] = colors[0]; g[-1][-1] = colors[1 % len(colors)]
    return g


def generate_task(seed, *, difficulty="medium"):
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty)
    f = _factor_for(ctx, difficulty)
    colors = list(ctx.draw_distinct_colors("colors", n=ctx.draw_int("ncol", 2, 5),
                                           exclude=[0]))
    n_train = ctx.draw_int("n_train", 3, 4)
    n_test = ctx.draw_int("n_test", 1, 2)
    program = f"(rule! (lambda (g) (downscale g {f})))"

    s_max = max(2, 30 // f)                      # input side = small*f <= 30
    pairs = []
    for idx in range(n_train + n_test):
        s = ctx.draw_int(f"s_{idx}", 2, min(s_max, 8))
        small = _build_small(ctx, idx, colors, s)
        gin = _upscale(small, f)                 # block-uniform big input
        pairs.append({"input": gin, "output": _downscale(gin, f)})
    return {"train": pairs[:n_train], "test": pairs[n_train:], "program": program,
            "chain": ["downscale"], "meta": {"difficulty": difficulty, "factor": f}}


if __name__ == "__main__":
    parity_check(generate_task, n=25, version_label=VERSION)
