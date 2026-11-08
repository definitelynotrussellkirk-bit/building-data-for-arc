"""gen2: slide every object to a wall — direction FIXED per task, varying across
seeds (one of up / down / left / right). Whole-object `move-to-wall`, shape
preserved (NOT per-cell gravity).

Layout adapts to the motion axis so objects never collide:
  - up / down   -> DISJOINT COLUMN LANES (no two objects share a column)
  - left / right-> DISJOINT ROW LANES    (no two objects share a row)
Component count is therefore preserved exactly.

Program (one rule, shared by all pairs; DIR is the per-task direction):
    (let ([objs (objects g)])
      (foldl (lambda (o acc) (move-to-wall acc (obj-cells o) 'DIR)) g objs))
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.generic.concepts.dense_motion import (
    parity_check, components)

VERSION = "1.1.0"
TASK_ID = "generic_dense_motion_gen2"


def _program(direction, bg_color):
    return ("(rule! (lambda (g) "
            f"(let ([objs (objects g {bg_color})]) "
            f"(foldl (lambda (o acc) (move-to-wall acc (obj-cells o) '{direction} {bg_color})) "
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


def _build_input(ctx, idx, palette, direction, bg_color):
    h, w = _grid_dims(ctx, idx)
    rng = ctx.draw_rng(f"layout_{idx}")
    g = [[bg_color] * w for _ in range(h)]

    if direction in ("down", "up"):
        # column lanes
        n_obj = rng.randint(6, min(11, w // 2))
        band_w = w // n_obj
        max_bh = min(4, h - 2)
        for i in range(n_obj):
            band_start = i * band_w
            max_bw = max(1, band_w - 1)
            blob = _random_blob(rng, max_bh, max_bw, 3, min(9, max_bh * max_bw))
            bh = max(p[0] for p in blob) + 1
            if direction == "down":
                top = rng.randint(0, h - 1 - bh)          # bottom <= h-2 -> falls
            else:
                top = rng.randint(1, h - bh)              # top >= 1 -> rises
            color = rng.choice(palette)
            for (pr, pc) in blob:
                g[top + pr][band_start + pc] = color
    else:
        # row lanes
        n_obj = rng.randint(6, min(11, h // 2))
        band_h = h // n_obj
        max_bw = min(4, w - 2)
        for i in range(n_obj):
            band_start = i * band_h
            max_bh = max(1, band_h - 1)
            blob = _random_blob(rng, max_bh, max_bw, 3, min(9, max_bh * max_bw))
            bw = max(p[1] for p in blob) + 1
            if direction == "left":
                left = rng.randint(1, w - bw)             # min_c >= 1 -> slides
            else:
                left = rng.randint(0, w - 1 - bw)         # max_c <= w-2 -> slides
            color = rng.choice(palette)
            for (pr, pc) in blob:
                g[band_start + pr][left + pc] = color
    return g


def _apply(g, direction, bg_color):
    h, w = len(g), len(g[0])
    out = [row[:] for row in g]
    for v, cells in components(g, bg=bg_color):
        if direction == "down":
            k = min(h - 1 - r for (r, c) in cells)
            dr, dc = k, 0
        elif direction == "up":
            k = min(r for (r, c) in cells)
            dr, dc = -k, 0
        elif direction == "left":
            k = min(c for (r, c) in cells)
            dr, dc = 0, -k
        else:                                             # right
            k = min(w - 1 - c for (r, c) in cells)
            dr, dc = 0, k
        for (r, c) in cells:
            out[r][c] = bg_color
        for (r, c) in cells:
            out[r + dr][c + dc] = v
    return out


def generate_task(seed, *, difficulty="medium"):
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty)
    direction = ctx.draw_choice("direction", ["down", "up", "left", "right"])
    bg_color = ctx.draw_color("bg_color", exclude=[0])
    n_colors = ctx.draw_int("n_colors", 4, 6)
    palette = list(ctx.draw_distinct_colors("palette", n=n_colors, exclude=[0, bg_color]))
    n_train = ctx.draw_int("n_train", 3, 4)
    n_test = ctx.draw_int("n_test", 1, 2)

    pairs = []
    for idx in range(n_train + n_test):
        gin = _build_input(ctx, idx, palette, direction, bg_color)
        gout = _apply(gin, direction, bg_color)
        if gout == gin:
            continue
        pairs.append({"input": gin, "output": gout})

    return {
        "train": pairs[:n_train],
        "test": pairs[n_train:n_train + n_test],
        "program": _program(direction, bg_color),
        "chain": ["objects", f"move_to_wall_{direction}", "nonzero_background"],
        "meta": {"difficulty": difficulty, "direction": direction,
                 "bg_color": bg_color, "palette": palette, "version": VERSION},
    }


if __name__ == "__main__":
    parity_check(generate_task, n=25, version_label=VERSION)
