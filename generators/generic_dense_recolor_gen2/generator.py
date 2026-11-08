"""gen2: per-object recolor by SHAPE CLASS.

Transform: each object is repainted by what KIND of shape it is —
  - a solid square (N x N filled)        -> colour SQ
  - a straight line (1 row or 1 column)  -> colour LN
  - anything else (rectangles, L/T/blobs)-> colour OT
Input objects all share ONE neutral colour, so the rule is "sort the
blobs into square / line / other and colour by class".

Racket: foldl over (objects g); per object a cond on (square? o),
(or (hline? o) (vline? o)), else; recolor-cells repaints the cells.
Classification is per-object and order-independent.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.generic.concepts.dense_recolor import (
    components, random_blob, place_shapes, parity_and_stats,
)

VERSION = "1.1.0"
TASK_ID = "generic_dense_recolor_gen2"


def _dims_for(difficulty):
    if difficulty == "easy":
        return (16, 18), (2, 3)
    if difficulty == "hard":
        return (20, 22), (3, 4)
    return (17, 21), (2, 4)            # medium (per-class counts)


def _classify(cells):
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    h = max(rs) - min(rs) + 1
    w = max(cs) - min(cs) + 1
    s = len(cells)
    if h == w and s == h * w:
        return "square"
    if h == 1 or w == 1:
        return "line"
    return "other"


def _apply(g, sq_c, ln_c, ot_c, bg=0):
    out = [row[:] for row in g]
    for _, cells in components(g, bg=bg):
        cls = _classify(cells)
        color = sq_c if cls == "square" else ln_c if cls == "line" else ot_c
        for r, c in cells:
            out[r][c] = color
    return out


def _square_shape(rng):
    n = rng.choice([2, 3])
    return [(r, c) for r in range(n) for c in range(n)]


def _line_shape(rng):
    k = rng.randint(3, 6)
    return [(0, c) for c in range(k)] if rng.random() < 0.5 \
        else [(r, 0) for r in range(k)]


def _other_shape(rng):
    # blob whose bbox is >=2x2 and is neither a filled square nor a line
    for _ in range(60):
        cells = random_blob(rng, rng.randint(3, 8))
        if _classify(cells) == "other":
            return cells
    # fallback: an L-tromino (bbox 2x2, size 3 -> "other")
    return [(0, 0), (1, 0), (1, 1)]


def _build_input(ctx, idx, in_color, counts, gh, gw, bg=0):
    rng = ctx.draw_rng(f"input_{idx}")
    n_sq, n_ln, n_ot = counts
    shapes = ([_square_shape(rng) for _ in range(n_sq)]
              + [_line_shape(rng) for _ in range(n_ln)]
              + [_other_shape(rng) for _ in range(n_ot)])
    rng.shuffle(shapes)
    grid, placed = place_shapes(rng, gh, gw, shapes, in_color)
    if bg != 0:
        # Keep the same isolated-shape layout but make the modal field color
        # nonzero.  The Racket program below passes this literal background to
        # `objects`, so the field itself is not mistaken for an object.
        grid = [[bg if v == 0 else v for v in row] for row in grid]
    return grid, placed


def generate_task(seed, *, difficulty="medium"):
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty)
    (glo, ghi), (clo, chi) = _dims_for(difficulty)

    use_nonzero_bg = ctx.draw_int("bg_axis", 0, 2) > 0
    bg = ctx.draw_color("bg", exclude=[0]) if use_nonzero_bg else 0
    in_color, sq_c, ln_c, ot_c = ctx.draw_distinct_colors(
        "palette", n=4, exclude=[0, bg])
    n_train = ctx.draw_int("n_train", 3, 4)
    n_test = ctx.draw_int("n_test", 1, 2)
    # fixed per-class counts across all pairs of this task
    counts = (ctx.draw_int("n_sq", clo, chi),
              ctx.draw_int("n_ln", clo, chi),
              ctx.draw_int("n_ot", clo, chi))

    program = (
        "(rule! (lambda (g) "
        "(foldl (lambda (o acc) "
        "(recolor-cells acc (obj-cells o) "
        f"(cond ((square? o) {sq_c}) "
        f"((or (hline? o) (vline? o)) {ln_c}) "
        f"(else {ot_c})))) g (objects g {bg}))))"
    )

    pairs = []
    for idx in range(n_train + n_test):
        gh = ctx.draw_int(f"gh_{idx}", glo, ghi)
        gw = ctx.draw_int(f"gw_{idx}", glo, ghi)
        gin, placed = _build_input(ctx, idx, in_color, counts, gh, gw, bg=bg)
        assert placed >= 6, f"only {placed} objects placed"
        gout = _apply(gin, sq_c, ln_c, ot_c, bg=bg)
        pairs.append({"input": gin, "output": gout})

    return {
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": program,
        "chain": ["objects", "recolor_by_shape_class"],
        "meta": {"difficulty": difficulty, "bg": bg, "nonzero_bg": bool(bg),
                 "in_color": in_color, "square": sq_c, "line": ln_c, "other": ot_c,
                 "version": VERSION},
    }



def self_check_task(task) -> list[str]:
    """Executable invariants for generated dense-recolor tasks.

    `scripts/generator_selfcheck.py generic_dense_recolor_gen2` calls this on
    whole generated tasks because generic concept generators emit train/test
    episodes rather than a single input grid.
    """
    msgs: list[str] = []
    meta = task.get("meta", {})
    bg = meta.get("bg", 0)
    sq_c = meta.get("square")
    ln_c = meta.get("line")
    ot_c = meta.get("other")
    expected = {sq_c, ln_c, ot_c}
    if len(expected) != 3 or bg in expected or 0 in expected:
        msgs.append("square/line/other output colors must be distinct non-bg nonzero colors")
    total_pairs = 0
    for split in ("train", "test"):
        for pair in task.get(split, []):
            total_pairs += 1
            gin = pair.get("input")
            gout = pair.get("output")
            if not gin or not gout or len(gin) != len(gout) or len(gin[0]) != len(gout[0]):
                msgs.append(f"{split} pair has missing or mismatched input/output dimensions")
                continue
            comps = components(gin, bg=bg)
            if len(comps) < 6:
                msgs.append(f"{split} pair has only {len(comps)} objects; expected >=6")
            want = _apply(gin, sq_c, ln_c, ot_c, bg=bg)
            if gout != want:
                msgs.append(f"{split} pair output does not match Python shape-class recolor mirror")
            out_colors = {v for row in gout for v in row if v != bg}
            if not out_colors <= expected:
                msgs.append(f"{split} pair has unexpected output colors {sorted(out_colors - expected)}")
            if len(out_colors & expected) < 3:
                msgs.append(f"{split} pair does not exercise all three shape classes")
    if total_pairs < 4:
        msgs.append(f"too few train/test pairs: {total_pairs}")
    return msgs


if __name__ == "__main__":
    parity_and_stats(generate_task, n=25, version_label=VERSION)
