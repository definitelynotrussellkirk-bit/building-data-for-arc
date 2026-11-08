"""gen1: LEARN A COLOR REMAP and apply it across a fully-colored grid.

Transform: every cell's color is mapped through a fixed bijection over the
palette (`recolor-map`), applied simultaneously to the whole grid. The input is
a 100%-filled grid of a few large contiguous color regions; the output is the
same grid with every color swapped per the learned map. The model must infer the
bijection from the demo pairs and apply it to the query.

Density concept: a DENSE (fully colored), LOW-component field — directly closes
the eval fill-density gap (eval ~73% filled vs the pool's old ~12%).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.generic.concepts.dense_field import (
    parity_check, measure, make_dense_partition,
)

VERSION = "1.1.0"
TASK_ID = "generic_dense_field_gen1"


def _size_for(difficulty):
    if difficulty == "easy":
        return (12, 18)
    if difficulty == "hard":
        return (22, 29)        # reach eval's large-grid tail, fully filled
    return (16, 24)            # medium


def _apply(g, cmap):
    """Mirror `((recolor-map {cmap}) g)`: every cell color -> cmap[color],
    simultaneously (a colors not in the map are left unchanged)."""
    return [[cmap.get(v, v) for v in row] for row in g]


def _fmt_cond(cmap):
    """Explicit per-color cond (no dict literal — the bridge mis-applies `{...}`
    as a procedure). `(cond ((= v k) val) ... (else v))`."""
    clauses = " ".join(f"((= v {k}) {val})" for k, val in cmap.items())
    return f"(cond {clauses} (else v))"


def _nontrivial_partition(ctx, key, gh, gw, palette):
    """Dense partition with at least two visible colors.

    A random 2x2 coarse partition can collapse to one color. That is a bad
    teaching example for a recolor-map task because the demo does not expose the
    palette mapping, and the inspector flags it as single-color output. Resample
    a few times; if unlucky, force one cell to a second palette color.
    """
    for attempt in range(8):
        g = make_dense_partition(ctx.draw_rng(f"{key}_try{attempt}"), gh, gw, palette)
        if len({v for row in g for v in row}) >= 2:
            return g
    g = make_dense_partition(ctx.draw_rng(f"{key}_fallback"), gh, gw, palette)
    first = g[0][0]
    alt = next(c for c in palette if c != first)
    g[-1][-1] = alt
    return g


def generate_task(seed, *, difficulty="medium"):
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty)
    slo, shi = _size_for(difficulty)

    n_pal = ctx.draw_int("n_palette", 4, 6)
    palette = list(ctx.draw_distinct_colors("palette", n=n_pal, exclude=[0]))
    n_train = ctx.draw_int("n_train", 3, 4)
    n_test = ctx.draw_int("n_test", 1, 2)

    # One fixed bijection over the palette (the rule the model must learn).
    # Do NOT use an unconstrained shuffle here: it occasionally produces fixed
    # points, and a fully identity shuffle makes the whole task output==input.
    # A nonzero cyclic shift is a derangement over this palette, so every input
    # color changes and the generator cannot teach a no-op recolor rule.
    shift = ctx.draw_int("cmap_shift", 1, n_pal - 1)
    cmap = {palette[i]: palette[(i + shift) % n_pal] for i in range(len(palette))}

    # simultaneous per-cell remap via grid-from-fn + cond (parity-safe; a plain
    # dict literal trips the bridge's dict-as-procedure crash).
    program = ("(rule! (lambda (g) (grid-from-fn (rows g) (cols g) "
               f"(lambda (r c) (let ((v (cell-at g r c))) {_fmt_cond(cmap)})))))")

    pairs = []
    for idx in range(n_train + n_test):
        gh = ctx.draw_int(f"gh_{idx}", slo, shi)
        gw = ctx.draw_int(f"gw_{idx}", slo, shi)
        gin = _nontrivial_partition(ctx, f"input_{idx}", gh, gw, palette)
        gout = _apply(gin, cmap)
        pairs.append({"input": gin, "output": gout})

    return {
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": program,
        "chain": ["recolor_map"],
        "meta": {"difficulty": difficulty, "palette": palette,
                 "cmap": cmap, "version": VERSION},
    }


if __name__ == "__main__":
    parity_check(generate_task, n=25, version_label=VERSION)
    measure(generate_task, n=25)


def self_check_task(task) -> list[str]:
    """Executable invariants for dense recolor-map tasks."""
    errors = []
    pairs = list(task.get("train", [])) + list(task.get("test", []))
    meta = task.get("meta", {})
    cmap = meta.get("cmap", {})
    palette = set(meta.get("palette", []))
    if not pairs:
        return ["task has no pairs"]
    if not cmap:
        errors.append("missing recolor map in task meta")
    if any(cmap.get(c, c) == c for c in palette):
        errors.append("recolor map must be a derangement over the visible palette")
    for idx, pair in enumerate(pairs):
        gin = pair.get("input")
        gout = pair.get("output")
        if not gin or not gin[0]:
            errors.append(f"pair {idx}: empty input")
            continue
        h, w = len(gin), len(gin[0])
        if len(gout) != h or any(len(row) != w for row in gout):
            errors.append(f"pair {idx}: output dimensions do not match input")
        in_colors = {v for row in gin for v in row}
        if 0 in in_colors:
            errors.append(f"pair {idx}: dense-field input unexpectedly contains background 0")
        if len(in_colors) < 2:
            errors.append(f"pair {idx}: input exposes fewer than two colors")
        expected = _apply(gin, cmap)
        if gout != expected:
            errors.append(f"pair {idx}: output is not the meta recolor-map application")
    return errors
