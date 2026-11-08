"""gen4: DENSE DOWNSCALE — collapse a zoomed-in, fully-colored field.

Transform: the input is a 100%-filled grid built of uniform K x K blocks (a
small dense partition upscaled by K); the rule downscales by K, recovering the
small grid. Program: `(downscale g K)` (no fn -> takes each block's top-left
cell, which is the block color since blocks are uniform -> byte-exact parity).

Why this gen (vs resize/gen2's downscale): resize/gen2 fills its small grid only
~60% (40% background), so its INPUT is sparse. This one's input is FULLY filled
by a few large regions, so it closes BOTH gaps at once -- fill DENSITY (eval ~73%
vs pool's old ~12%) AND the size-SHRINK gap (output smaller than input, ~0 in the
pool) -- while keeping a LOW component count (eval-like, not pixel noise). The
hard tier reaches the large-grid tail (input up to ~27 wide, fully colored).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.generic.concepts.dense_field import (
    parity_check, measure, make_dense_partition,
)

VERSION = "1.1.0"
TASK_ID = "generic_dense_field_gen4"


def _nontrivial_small(rng, gh, gw, palette):
    """A small dense partition with >= 2 colors (so downscale isn't constant).

    The output equals this small grid; if make_dense_partition collapses it to a
    single coarse-tile color, the downscaled output is monochrome — a constant,
    not a recognizable downscale. Resample, then force a second color as fallback.
    """
    for _ in range(8):
        small = make_dense_partition(rng, gh, gw, palette)
        if len({v for row in small for v in row}) >= 2:
            return small
    a = small[0][0]
    small[-1][-1] = next(c for c in palette if c != a)
    return small


def _small_size(difficulty):
    """Side of the small (output) grid BEFORE upscaling."""
    if difficulty == "easy":
        return (5, 7)
    if difficulty == "hard":
        return (8, 11)
    return (6, 9)


def _upscale(g, f):
    out = []
    for row in g:
        big = [v for v in row for _ in range(f)]
        for _ in range(f):
            out.append(big[:])
    return out


def _downscale(g, f):
    # top-left of each fxf block (matches prelude `downscale` default reduction)
    return [[g[r * f][c * f] for c in range(len(g[0]) // f)]
            for r in range(len(g) // f)]


def generate_task(seed, *, difficulty="medium"):
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty)
    slo, shi = _small_size(difficulty)

    # factor: keep upscaled input side <= 29 (small_max * f).
    f = ctx.draw_int("factor", 2, 4) if difficulty != "hard" else ctx.draw_int("factor", 2, 3)
    n_pal = ctx.draw_int("n_palette", 4, 6)
    palette = list(ctx.draw_distinct_colors("palette", n=n_pal, exclude=[0]))
    n_train = ctx.draw_int("n_train", 3, 4)
    n_test = ctx.draw_int("n_test", 1, 2)
    program = f"(rule! (lambda (g) (downscale g {f})))"

    pairs = []
    for idx in range(n_train + n_test):
        r = ctx.draw_rng(f"input_{idx}")
        gh = ctx.draw_int(f"gh_{idx}", slo, min(shi, 29 // f))
        gw = ctx.draw_int(f"gw_{idx}", slo, min(shi, 29 // f))
        small = _nontrivial_small(r, gh, gw, palette)      # dense, low-component, >=2 colors
        gin = _upscale(small, f)                           # dense, blocky, large
        pairs.append({"input": gin, "output": _downscale(gin, f)})

    return {
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": program,
        "chain": ["downscale"],
        "meta": {"difficulty": difficulty, "factor": f, "palette": palette,
                 "nonconstant_output_guard": True, "version": VERSION},
    }


if __name__ == "__main__":
    parity_check(generate_task, n=25, version_label=VERSION)
    measure(generate_task, n=25)
