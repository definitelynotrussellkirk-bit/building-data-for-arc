"""gen3: NON-UNIFORM scale — each row repeated by a per-row ratio and each
column by a per-col ratio (various ratios 1..3, fixed per task). Program:
(scale-map g (list row-ratios...) (list col-ratios...)). All pairs in a task
share input dims so the same ratio lists apply; content varies. Covers
asymmetric/stretch resizes (different vertical vs horizontal blow-up)."""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.generic.concepts.resize import parity_check

VERSION = "1.0.0"
TASK_ID = "generic_resize_scalemap"


def _scale_map(g, row_scales, col_scales):
    out = []
    for i, row in enumerate(g):
        expanded = []
        for j, v in enumerate(row):
            expanded.extend([v] * col_scales[j])
        for _ in range(row_scales[i]):
            out.append(expanded[:])
    return out


def _build_input(ctx, idx, colors, h, w):
    rng = ctx.draw_rng(f"input_{idx}")
    g = [[(rng.choice(colors) if rng.random() < 0.6 else 0) for _ in range(w)]
         for _ in range(h)]
    if len({v for row in g for v in row} - {0}) < 2:
        g[0][0] = colors[0]; g[-1][-1] = colors[1 % len(colors)]
    return g


def generate_task(seed, *, difficulty="medium"):
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty)
    if difficulty == "easy":
        h = ctx.draw_int("h", 3, 4); w = ctx.draw_int("w", 3, 4); rmax = 2
    elif difficulty == "hard":
        h = ctx.draw_int("h", 4, 6); w = ctx.draw_int("w", 4, 6); rmax = 3
    else:
        h = ctx.draw_int("h", 3, 5); w = ctx.draw_int("w", 3, 5); rmax = 3
    colors = list(ctx.draw_distinct_colors("colors", n=ctx.draw_int("ncol", 2, 5),
                                           exclude=[0]))
    # per-row / per-col ratios fixed for the whole task; ensure non-identity and
    # output dims (sum of ratios on each axis) stay <= 30.
    rscale = ctx.draw_rng("rscale")
    row_scales = [rscale.randint(1, rmax) for _ in range(h)]
    col_scales = [rscale.randint(1, rmax) for _ in range(w)]
    if sum(row_scales) == h and sum(col_scales) == w:      # both identity -> bump one
        row_scales[0] = min(rmax, 2)
    while sum(row_scales) > 30: row_scales[row_scales.index(max(row_scales))] -= 1
    while sum(col_scales) > 30: col_scales[col_scales.index(max(col_scales))] -= 1

    n_train = ctx.draw_int("n_train", 3, 4)
    n_test = ctx.draw_int("n_test", 1, 2)
    rs = " ".join(str(x) for x in row_scales)
    cs = " ".join(str(x) for x in col_scales)
    program = f"(rule! (lambda (g) (scale-map g (list {rs}) (list {cs}))))"

    pairs = []
    for idx in range(n_train + n_test):
        gin = _build_input(ctx, idx, colors, h, w)
        pairs.append({"input": gin, "output": _scale_map(gin, row_scales, col_scales)})
    return {"train": pairs[:n_train], "test": pairs[n_train:], "program": program,
            "chain": ["scale_map"],
            "meta": {"difficulty": difficulty, "row_scales": row_scales,
                     "col_scales": col_scales}}


if __name__ == "__main__":
    parity_check(generate_task, n=25, version_label=VERSION)
