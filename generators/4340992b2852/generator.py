"""Generator for a1570a43.

Rule: 4 green markers form rect corners; red shape exists elsewhere;
rule centers shape inside marker rectangle.

Combinatorial axes (8): grid_h/w, rect_h, rect_w, shape_h, shape_w,
position_bias, palette_kind, anchor_corner.
Degenerates: shape_inside, no_shape, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import components as _components

GENERATOR_ID = "4340992b2852"
VERSION = "1.1.0"
TASK_ID = "4340992b2852"
SUMMARY = "4 green corner markers + a red shape; rule centers the shape inside marker-rect."

INVARIANTS = [
    "background is 0",
    "exactly 4 green(3) cells at corners of a rectangle (2 distinct rows, 2 distinct cols)",
    ">=2 red(2) cells in a contiguous L-/T-/staircase-like shape",
    "red shape's bbox fits inside the green rectangle",
    "red shape doesn't overlap the green rectangle's interior in the input",
]

POSITION_BIASES = ("scattered", "centered", "corner", "near_edge")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("shape_inside", "no_shape", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {'grid_h': {'type': 'int', 'default': 'rng 10..14', 'valid': '8..18'},
 'grid_w': {'type': 'int', 'default': 'rng 10..14', 'valid': '8..18'},
 'rect_h': {'type': 'int', 'default': 'rng 5..7', 'valid': '4..h-3'},
 'rect_w': {'type': 'int', 'default': 'rng 5..7', 'valid': '4..w-3'},
 'shape_h': {'type': 'int', 'default': 'rng 2..rh-2', 'valid': '2..rh-2'},
 'shape_w': {'type': 'int', 'default': 'rng 2..rw-2', 'valid': '2..rw-2'},
 'position_bias': {'type': 'str',
                   'default': 'rng helpful',
                   'valid': 'scattered|centered|corner|near_edge'},
 'palette_kind': {'type': 'str', 'default': 'fixed', 'valid': 'fixed'},
 'texture': {'type': 'str',
             'default': 'alias for position_bias',
             'valid': 'scattered|centered|corner|near_edge|shape_inside|no_shape|full_grid'}}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 8, 10
        rh_lo, rh_hi = 4, 5
    elif difficulty == "hard":
        h_lo, h_hi = 14, 18
        rh_lo, rh_hi = 6, 9
    else:
        h_lo, h_hi = 10, 14
        rh_lo, rh_hi = 5, 7
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rh = ctx.draw_int("rect_h", rh_lo, min(rh_hi, h - 3))
    rw = ctx.draw_int("rect_w", rh_lo, min(rh_hi, w - 3))
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias", list(POSITION_BIASES)))
    for _layout in range(80):
        rr, rc = _pick_rect_pos(bias, h, w, rh, rw, rng)
        g = full_grid(h, w, 0)
        g[rr][rc] = 3
        g[rr][rc + rw - 1] = 3
        g[rr + rh - 1][rc] = 3
        g[rr + rh - 1][rc + rw - 1] = 3
        sh_h = int(overrides.get("shape_h",
                                 rng.randint(2, max(2, rh - 2))))
        sh_w = int(overrides.get("shape_w",
                                 rng.randint(2, max(2, rw - 2))))
        sh_h = max(2, min(sh_h, rh - 2))
        sh_w = max(2, min(sh_w, rw - 2))
        shape_cells = [(sr, sc) for sr in range(sh_h) for sc in range(min(sr + 2, sh_w))]
        candidates = []
        for or_ in range(h - sh_h + 1):
            for oc in range(w - sh_w + 1):
                overlaps_rect = any(
                    rr <= or_ + sr <= rr + rh - 1 and rc <= oc + sc <= rc + rw - 1
                    for sr, sc in shape_cells
                )
                if not overlaps_rect:
                    candidates.append((or_, oc))
        if candidates:
            or_, oc = candidates[rng.randint(0, len(candidates) - 1)]
            for sr, sc in shape_cells:
                g[or_ + sr][oc + sc] = 2
            return g
    raise ValueError("could not place red shape outside the marker rectangle")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    greens = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3]
    if len(greens) != 4 or len({r for r, _ in greens}) != 2 or len({c for _, c in greens}) != 2:
        errors.append("expected exactly four green markers at rectangle corners")
        return errors
    r1, c1 = min(r for r, _ in greens), min(c for _, c in greens)
    r2, c2 = max(r for r, _ in greens), max(c for _, c in greens)
    reds = [comp for comp in _components(grid, colors={2})]
    if len(reds) != 1 or len(reds[0]["cells"]) < 2:
        errors.append("expected one multi-cell red shape")
        return errors
    br1, bc1, br2, bc2 = reds[0]["bbox"]
    if br2 - br1 + 1 > r2 - r1 - 1 or bc2 - bc1 + 1 > c2 - c1 - 1:
        errors.append("red shape bbox must fit inside the green rectangle")
    if any(r1 < r < r2 and c1 < c < c2 for r, c in reds[0]["cells"]):
        errors.append("input red shape should start outside the marker rectangle")
    return errors


def _pick_rect_pos(bias, h, w, rh, rw, rng):
    max_r = max(1, h - rh - 1)
    max_c = max(1, w - rw - 1)
    if bias == "centered":
        rr = max(1, (h - rh) // 2)
        rc = max(1, (w - rw) // 2)
    elif bias == "corner":
        rr = rng.choice([1, max_r])
        rc = rng.choice([1, max_c])
    elif bias == "near_edge":
        if rng.random() < 0.5:
            rr = rng.choice([1, max_r])
            rc = rng.randint(1, max_c)
        else:
            rr = rng.randint(1, max_r)
            rc = rng.choice([1, max_c])
    else:
        rr = rng.randint(1, max_r)
        rc = rng.randint(1, max_c)
    rr = max(1, min(rr, max_r))
    rc = max(1, min(rc, max_c))
    return rr, rc


def _draw_from_degenerate(name, rng):
    h, w = 12, 12
    g = full_grid(h, w, 0)
    if name == "shape_inside":
        rr, rc, rh, rw = 2, 2, 6, 7
        g[rr][rc] = 3; g[rr][rc + rw - 1] = 3
        g[rr + rh - 1][rc] = 3; g[rr + rh - 1][rc + rw - 1] = 3
        g[4][4] = 2; g[4][5] = 2; g[5][5] = 2
        return g
    if name == "no_shape":
        rr, rc, rh, rw = 2, 2, 5, 5
        g[rr][rc] = 3; g[rr][rc + rw - 1] = 3
        g[rr + rh - 1][rc] = 3; g[rr + rh - 1][rc + rw - 1] = 3
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 3
        return g
    return g
