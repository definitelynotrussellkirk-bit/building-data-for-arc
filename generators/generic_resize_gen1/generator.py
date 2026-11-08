"""gen1: UPSCALE by an integer factor (ratios 2..5, fixed per task, varied
across tasks). Output = each input cell expanded to a factor x factor block.
Program: (upscale g F). A different random colored field per pair; the shared
rule is "blow up by F"."""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.generic.concepts.resize import parity_check

VERSION = "1.1.0"
TASK_ID = "generic_resize_upscale"


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


def _build_input(ctx, idx, colors, s, bg):
    rng = ctx.draw_rng(f"input_{idx}")
    # Use a nonzero modal background and a moderate foreground density. The
    # first version used literal 0 as background with p(foreground)=0.6, which
    # made this resize stressor both black-bg-heavy and much denser than the
    # modal-background eval target. Upscale is color-agnostic, so this preserves
    # the same rule while moving the output distribution toward eval-like
    # nonzero backgrounds and ~0.3 semantic occupancy.
    g = [[(rng.choice(colors) if rng.random() < 0.35 else bg) for _ in range(s)]
         for _ in range(s)]
    if len({v for row in g for v in row} - {bg}) < 2:      # force >=2 foreground colors
        g[0][0] = colors[0]; g[-1][-1] = colors[1 % len(colors)]
    return g


def generate_task(seed, *, difficulty="medium"):
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty)
    f = _factor_for(ctx, difficulty)
    # Match eval's nonzero-background convention in expectation rather than
    # making this generator all-colored-field: 2/3 nonzero-bg, 1/3 black-bg.
    use_nonzero_bg = ctx.draw_int("nonzero_bg_roll", 0, 2) > 0
    bg = ctx.draw_color("bg", exclude=[0]) if use_nonzero_bg else 0
    colors = list(ctx.draw_distinct_colors("colors", n=ctx.draw_int("ncol", 2, 5),
                                           exclude=[bg]))
    n_train = ctx.draw_int("n_train", 3, 4)
    n_test = ctx.draw_int("n_test", 1, 2)
    program = f"(rule! (lambda (g) (upscale g {f})))"

    s_max = max(3, 30 // f)                     # keep output side <= 30
    pairs = []
    for idx in range(n_train + n_test):
        s = ctx.draw_int(f"s_{idx}", 3, min(s_max, 8))
        gin = _build_input(ctx, idx, colors, s, bg)
        pairs.append({"input": gin, "output": _upscale(gin, f)})
    return {"train": pairs[:n_train], "test": pairs[n_train:], "program": program,
            "chain": ["upscale"], "meta": {"difficulty": difficulty, "factor": f, "bg": bg}}


if __name__ == "__main__":
    parity_check(generate_task, n=25, version_label=VERSION)
