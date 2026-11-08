"""gen3: magnetism to a central bar. A full-height WALL line (one fixed color)
splits the grid; every object slides HORIZONTALLY toward the wall until it is
flush against it (whole-object `slide-until-contact`, shape preserved).

Layout: objects live in DISJOINT ROW LANES (no two share a row) and each sits
entirely on one side of the wall with a >=1 column gap. Direction per object is
derived in the rule from its side of the wall, so objects on the left slide
right and objects on the right slide left. The wall is a single component; the
object count + 1 (the wall) is preserved exactly.

Program (one rule, shared by all pairs; W is the wall color, B is background):
    (let* ([wallcol (for/first ([c (in-range (cols g))]
                       #:when (andmap (lambda (r) (= (cell-at g r c) W))
                                      (range 0 (rows g)))) c)]
           [wall-cells (for/list ([r (in-range (rows g))]) (list r wallcol))]
           [objs (filter (lambda (o) (not (= (obj-color o) W))) (objects g B))])
      (foldl (lambda (o acc)
               (let ([dir (if (< (second (obj-bbox o)) wallcol) 'right 'left)])
                 (slide-until-contact acc (obj-cells o) wall-cells dir B)))
             g objs))
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.generic.concepts.dense_motion import (
    parity_check, components)

VERSION = "1.1.0"
TASK_ID = "generic_dense_motion_gen3"


def _program(wall_color, bg_color):
    return (
        "(rule! (lambda (g) "
        "(let* ([wallcol (for/first ([c (in-range (cols g))] "
        f"#:when (andmap (lambda (r) (= (cell-at g r c) {wall_color})) "
        "(range 0 (rows g)))) c)] "
        "[wall-cells (for/list ([r (in-range (rows g))]) (list r wallcol))] "
        f"[objs (filter (lambda (o) (not (= (obj-color o) {wall_color}))) "
        f"(objects g {bg_color}))]) "
        "(foldl (lambda (o acc) "
        "(let ([dir (if (< (second (obj-bbox o)) wallcol) 'right 'left)]) "
        f"(slide-until-contact acc (obj-cells o) wall-cells dir {bg_color}))) "
        "g objs))))")


# --------------------------------------------------------------------------
def _random_blob(rng, max_h, max_w, min_cells, max_cells):
    target = rng.randint(min_cells, max_cells)
    cells = {(0, 0)}
    tries = 0
    while len(cells) < target and tries < 200:
        tries += 1
        br, bc = rng.choice(tuple(cells))
        dr, dc = rng.choice(((-1, 0), (1, 0), (0, -1), (0, 1)))
        cand = cells | {(br + dr, bc + dc)}
        rs = [p[0] for p in cand]
        cs = [p[1] for p in cand]
        if (max(rs) - min(rs) + 1 <= max_h and max(cs) - min(cs) + 1 <= max_w):
            cells = cand
    mnr = min(p[0] for p in cells)
    mnc = min(p[1] for p in cells)
    return {(r - mnr, c - mnc) for r, c in cells}


def _grid_dims(ctx, idx):
    import math
    w = ctx.draw_int(f"w_{idx}", 20, 26)
    hmin = max(12, math.ceil(250 / w))
    hmax = min(20, 500 // w)
    h = ctx.draw_int(f"h_{idx}", hmin, hmax)
    return h, w


def _build_input(ctx, idx, palette, wall_color, bg_color):
    h, w = _grid_dims(ctx, idx)
    rng = ctx.draw_rng(f"layout_{idx}")
    g = [[bg_color] * w for _ in range(h)]
    wallcol = rng.randint(w // 3, (2 * w) // 3)
    for r in range(h):
        g[r][wallcol] = wall_color

    n_obj = rng.randint(6, min(11, h // 2))
    band_h = h // n_obj
    for i in range(n_obj):
        band_start = i * band_h
        max_bh = max(1, band_h - 1)
        max_bw = 4
        blob = _random_blob(rng, max_bh, max_bw, 3, min(9, max_bh * max_bw))
        bh = max(p[0] for p in blob) + 1
        bw = max(p[1] for p in blob) + 1
        # which side can fit this blob with a >=1 gap from the wall?
        left_ok = wallcol - 1 - bw >= 0          # rightmost col <= wallcol-2
        right_ok = w - bw >= wallcol + 2          # leftmost col >= wallcol+2
        sides = []
        if left_ok:
            sides.append("L")
        if right_ok:
            sides.append("R")
        if not sides:
            continue
        side = rng.choice(sides)
        if side == "L":
            left = rng.randint(0, wallcol - 1 - bw)
        else:
            left = rng.randint(wallcol + 2, w - bw)
        top = band_start + rng.randint(0, max_bh - bh)
        color = rng.choice(palette)
        for (pr, pc) in blob:
            g[top + pr][left + pc] = color
    return g


def _apply(g, wall_color, bg_color):
    h, w = len(g), len(g[0])
    wallcol = next(c for c in range(w)
                   if all(g[r][c] == wall_color for r in range(h)))
    out = [row[:] for row in g]
    for v, cells in components(g, bg=bg_color):
        if v == wall_color:
            continue
        c1 = min(c for (r, c) in cells)
        if c1 < wallcol:                          # slide right to the wall
            k = wallcol - 1 - max(c for (r, c) in cells)
            dc = k
        else:                                     # slide left to the wall
            k = min(c for (r, c) in cells) - wallcol - 1
            dc = -k
        for (r, c) in cells:
            out[r][c] = bg_color
        for (r, c) in cells:
            out[r][c + dc] = v
    return out


def generate_task(seed, *, difficulty="medium"):
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty)
    wall_color = ctx.draw_color("wall_color", exclude=[0])
    bg_color = ctx.draw_color("bg_color", exclude=[0, wall_color])
    n_colors = ctx.draw_int("n_colors", 4, 6)
    palette = list(ctx.draw_distinct_colors(
        "palette", n=n_colors, exclude=[0, wall_color, bg_color]))
    n_train = ctx.draw_int("n_train", 3, 4)
    n_test = ctx.draw_int("n_test", 1, 2)

    pairs = []
    for idx in range(n_train + n_test):
        gin = _build_input(ctx, idx, palette, wall_color, bg_color)
        gout = _apply(gin, wall_color, bg_color)
        if gout == gin:
            continue
        pairs.append({"input": gin, "output": gout})

    return {
        "train": pairs[:n_train],
        "test": pairs[n_train:n_train + n_test],
        "program": _program(wall_color, bg_color),
        "chain": ["objects", "slide_until_contact_wall", "nonzero_background"],
        "meta": {"difficulty": difficulty, "wall_color": wall_color,
                 "bg_color": bg_color, "palette": palette, "version": VERSION},
    }


def self_check_task(task) -> list[str]:
    """Verify the whole-task magnetism invariant for generated generic rows."""
    errs = []
    if not isinstance(task, dict):
        return ["task is not a dict"]
    meta = task.get("meta") or {}
    wall_color = meta.get("wall_color")
    bg_color = meta.get("bg_color")
    if wall_color is None or bg_color is None or wall_color == bg_color:
        errs.append("missing/distinct wall_color and bg_color in meta")
        return errs
    pairs = list(task.get("train") or []) + list(task.get("test") or [])
    if len(task.get("train") or []) < 3 or len(task.get("test") or []) < 1:
        errs.append("expected at least 3 train and 1 test pair")
    if not pairs:
        errs.append("task has no pairs")
        return errs
    saw_left = saw_right = False
    for pair in pairs:
        gin = pair.get("input") if isinstance(pair, dict) else None
        gout = pair.get("output") if isinstance(pair, dict) else None
        if not gin or not gout or len({len(r) for r in gin}) != 1:
            errs.append("pair has missing or ragged input/output grid")
            continue
        h, w = len(gin), len(gin[0])
        wallcols = [c for c in range(w) if all(gin[r][c] == wall_color for r in range(h))]
        if len(wallcols) != 1:
            errs.append("input must have exactly one full-height wall column")
            continue
        wallcol = wallcols[0]
        objs = [(v, cells) for v, cells in components(gin, bg=bg_color) if v != wall_color]
        if len(objs) < 3:
            errs.append("expected at least three moving objects")
        if gin == gout:
            errs.append("output equals input; no object moved")
        if len(components(gin, bg=bg_color)) != len(components(gout, bg=bg_color)):
            errs.append("component count changed after slide")
        for _, cells in objs:
            if max(c for _, c in cells) < wallcol:
                saw_left = True
            elif min(c for _, c in cells) > wallcol:
                saw_right = True
            else:
                errs.append("object overlaps or touches the wall column")
    if not (saw_left and saw_right):
        errs.append("task should demonstrate objects moving from both sides of the wall")
    return sorted(set(errs))


if __name__ == "__main__":
    parity_check(generate_task, n=25, version_label=VERSION)
