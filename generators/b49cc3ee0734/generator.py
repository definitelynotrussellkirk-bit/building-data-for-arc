"""Generator for arc_additional_puzzle_bank_volume2:M11.

The red marker selects the side whose object is mirrored across a gray divider.

Combinatorial axes (8): grid_h, grid_w, palette_kind, orientation,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_marker, no_divider, no_object.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b49cc3ee0734"
VERSION = "2.0.1"  # poison fix: object was a single fixed L-tromino in fixed
# color 7 always on the left/top side. Rule MIRRORS the shape, so shape is a
# key axis. v2 grows a random polyomino, varies object color {3,4,6,7,8,9},
# and places the object/marker on EITHER side of the divider.
TASK_ID = "b49cc3ee0734"
SUMMARY = "Full color-5 divider (row or col); red(2) marker is on the source side; rule mirrors all non-marker, non-divider cells on the marker's side across the divider, erases marker in output."

# Rivals: 'mirror to wrong side' refuted by ≥2 demos where marker
# clearly selects source side. 'preserve marker' refuted by any
# demo (marker erased). 'use bg for mirror' refuted by any demo
# (colors preserved). 'mirror across grid center, not divider'
# refuted by ≥2 demos with off-center divider.
# 4 demos with varied orientations + sides cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "there is exactly one full gray divider row or column",
    "the red marker is on the source side",
    "source-side non-marker cells reflect in bounds and preserve color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "no_divider", "no_object")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "6..24"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "6..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "orientation":    {"type": "str", "default": "rng vertical|horizontal",
                       "valid": "vertical|horizontal"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "marker_plus_object_one_side",
                       "valid": "marker_plus_object_one_side"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_marker|no_divider|no_object"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly 1 full gray(5) divider row or column; ≥1 red(2) marker cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    # Check for full gray divider row or column
    gray_rows = [r for r in range(h) if all(grid[r][c] == 5 for c in range(w))]
    gray_cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    n_dividers = len(gray_rows) + len(gray_cols)
    if n_dividers == 0:
        errs.append("expected ≥1 full gray(5) divider row or column; found none")
    # Check for red(2) marker
    red_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if not red_cells:
        errs.append("expected ≥1 red(2) marker cell; found none")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 7, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 18)
        w = ctx.draw_int("grid_w", 14, 18)
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 10, 13)
    rng = ctx.draw_rng("placement")
    vertical = rng.choice([True, False])
    obj_color = rng.choice([3, 4, 6, 7, 8, 9])

    for _outer in range(80):
        g = full_grid(h, w, 0)
        shape = _poly(rng, rng.randint(3, 6))
        rs = [r for r, _ in shape]
        cs = [c for _, c in shape]
        sh = max(rs) - min(rs) + 1
        sw = max(cs) - min(cs) + 1
        shape = [(r - min(rs), c - min(cs)) for r, c in shape]

        if vertical:
            d = rng.randint(3, w - 4)
            for r in range(h):
                g[r][d] = 5
            on_left = rng.choice([True, False])
            r0 = rng.randint(0, h - sh)
            if on_left:
                # object cols [c0, c0+sw-1] all < d; reflection cols
                # 2d-c must be < w  => c >= 2d-(w-1)
                lo = max(0, 2 * d - (w - 1))
                hi = d - sw
                if lo > hi:
                    continue
                c0 = rng.randint(lo, hi)
                mc = c0 + sw  # marker just right of object, still left of d? must be <d
                if mc >= d:
                    mc = max(0, c0 - 1)
            else:
                lo = d + 1
                hi = min(w - sw, 2 * d - 1)  # reflection col 2d-c >=0
                if lo > hi:
                    continue
                c0 = rng.randint(lo, hi)
                mc = c0 - 1 if c0 - 1 > d else min(w - 1, c0 + sw)
            for dr, dc in shape:
                g[r0 + dr][c0 + dc] = obj_color
            # place marker on the object's side, on a free cell
            _place_marker(g, r0, mc, d, vertical=True)
        else:
            d = rng.randint(3, h - 4)
            for c in range(w):
                g[d][c] = 5
            on_top = rng.choice([True, False])
            c0 = rng.randint(0, w - sw)
            if on_top:
                lo = max(0, 2 * d - (h - 1))
                hi = d - sh
                if lo > hi:
                    continue
                r0 = rng.randint(lo, hi)
                mr = r0 - 1 if r0 - 1 >= 0 else r0 + sh
            else:
                lo = d + 1
                hi = min(h - sh, 2 * d - 1)
                if lo > hi:
                    continue
                r0 = rng.randint(lo, hi)
                mr = min(h - 1, r0 + sh) if r0 + sh != d else r0 - 1
            for dr, dc in shape:
                g[r0 + dr][c0 + dc] = obj_color
            _place_marker(g, mr, c0, d, vertical=False)
        # validate exactly one marker present
        if any(2 in row for row in g):
            return g
    raise ValueError("could not realize mirror layout")


def _poly(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc))
            seen.add((nr, nc))
    return cells


def _place_marker(g, r, c, d, vertical):
    """Place the color-2 marker near (r,c), on the object's side of divider d,
    on a free cell. The rule only reads the marker's side, not exact spot."""
    h, w = len(g), len(g[0])
    for (rr, cc) in [(r, c), (r, c + 1), (r, c - 1), (r + 1, c), (r - 1, c),
                     (r + 1, c + 1), (r - 1, c - 1)]:
        if 0 <= rr < h and 0 <= cc < w and g[rr][cc] == 0:
            if vertical and cc == d:
                continue
            if (not vertical) and rr == d:
                continue
            g[rr][cc] = 2
            return


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_marker":
        # divider + object without red marker → which side is source ambiguous
        for r in range(h):
            g[r][4] = 5
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[2 + dr][1 + dc] = 7
        return g
    if name == "no_divider":
        # marker + object without gray divider → no axis to mirror across
        g[2][3] = 2
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[3 + dr][1 + dc] = 7
        return g
    if name == "no_object":
        # divider + marker but no object to mirror
        for r in range(h):
            g[r][4] = 5
        g[2][3] = 2
        return g
    return g
