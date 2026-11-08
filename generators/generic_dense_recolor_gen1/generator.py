"""gen1: per-object recolor by SIZE EXTREMES.

Transform: among the objects on the field, the UNIQUE largest one becomes
colour BIG, the UNIQUE smallest one becomes colour SMALL, and every other
object becomes colour MID. Input objects all share ONE neutral colour, so
the output reads as "rank the blobs by area, paint the extremes".

Racket: pick-max / pick-min over obj-size locate the extremes (object
identity via eq?); foldl + recolor-cells repaints each object's cells.

Object sizes are drawn DISTINCT so the max and min are unambiguous (a
prerequisite for pick-max/pick-min == the Python `size==max/min` test).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.generic.concepts.dense_recolor import (
    components, random_blob, place_shapes, parity_and_stats,
)

VERSION = "1.1.0"
TASK_ID = "generic_dense_recolor_gen1"


def _dims_for(difficulty):
    if difficulty == "easy":
        return (16, 18), (6, 7)
    if difficulty == "hard":
        return (20, 22), (8, 10)
    return (17, 21), (7, 9)            # medium


def _apply(g, big_c, small_c, mid_c, bg=0):
    comps = components(g, bg=bg)
    sizes = [len(cells) for _, cells in comps]
    smax, smin = max(sizes), min(sizes)
    out = [row[:] for row in g]
    for _, cells in comps:
        s = len(cells)
        color = big_c if s == smax else small_c if s == smin else mid_c
        for r, c in cells:
            out[r][c] = color
    return out


def _build_input(ctx, idx, in_color, n_obj, gh, gw, bg=0):
    rng = ctx.draw_rng(f"input_{idx}")
    # DISTINCT sizes 3..12 so the largest/smallest are unique.
    sizes = rng.sample(range(3, 13), n_obj)
    rng.shuffle(sizes)
    shapes = [random_blob(rng, s) for s in sizes]
    rng.shuffle(shapes)
    grid, placed = place_shapes(rng, gh, gw, shapes, in_color)
    if bg != 0:
        # Keep the same isolated-object placement semantics but make the field
        # background nonzero; the Racket program below passes this literal bg
        # into `objects`, so the large background is not treated as an object.
        grid = [[bg if v == 0 else v for v in row] for row in grid]
    return grid, placed


def generate_task(seed, *, difficulty="medium"):
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty)
    (glo, ghi), (nlo, nhi) = _dims_for(difficulty)

    bg = ctx.draw_color("bg", exclude=[0])
    in_color, big_c, small_c, mid_c = ctx.draw_distinct_colors(
        "palette", n=4, exclude=[0, bg])
    n_train = ctx.draw_int("n_train", 3, 4)
    n_test = ctx.draw_int("n_test", 1, 2)
    n_obj = ctx.draw_int("n_obj", nlo, nhi)

    program = (
        "(rule! (lambda (g) "
        f"(let* ((objs (objects g {bg})) "
        "(big (pick-max objs obj-size)) "
        "(small (pick-min objs obj-size))) "
        "(foldl (lambda (o acc) "
        f"(recolor-cells acc (obj-cells o) "
        f"(cond ((eq? o big) {big_c}) ((eq? o small) {small_c}) "
        f"(else {mid_c})))) g objs))))"
    )

    pairs = []
    for idx in range(n_train + n_test):
        gh = ctx.draw_int(f"gh_{idx}", glo, ghi)
        gw = ctx.draw_int(f"gw_{idx}", glo, ghi)
        gin, placed = _build_input(ctx, idx, in_color, n_obj, gh, gw, bg=bg)
        # need >=3 distinct-size objects so big/mid/small all appear
        assert placed >= 3, f"only {placed} objects placed"
        gout = _apply(gin, big_c, small_c, mid_c, bg=bg)
        pairs.append({"input": gin, "output": gout})

    return {
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": program,
        "chain": ["objects", "recolor_by_size_extremes"],
        "meta": {"difficulty": difficulty, "bg": bg, "in_color": in_color,
                 "big": big_c, "small": small_c, "mid": mid_c,
                 "version": VERSION},
    }


if __name__ == "__main__":
    parity_and_stats(generate_task, n=25, version_label=VERSION)
