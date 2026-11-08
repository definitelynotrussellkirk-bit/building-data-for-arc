"""Generator for 6855a6e4.

Rule: each gray shape mirrors across the closed back wall of its nearest
red C-shape (the wall opposite the C's opening).

Combinatorial axes: grid size, C size/position, opening direction, and
the gray shape / position near the opening.
Degenerates: no_C, no_gray, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "28d51fb858a1"
VERSION = "2.0.1"
TASK_ID = "28d51fb858a1"
SUMMARY = (
    "0-bg grid (size varies). A red (color-2) C-SHAPE: a rectangular "
    "outline (4..6 per side) with exactly ONE open side. A small GRAY "
    "(color-5) shape sits just outside the OPENING. Rule: mirror the gray "
    "shape across the C's CLOSED BACK WALL (the wall opposite the "
    "opening) — right-open reflects across the left wall, left-open "
    "across the right wall, down-open across the top wall, up-open across "
    "the bottom wall — removing the original gray and painting the mirror "
    "image. The grid size, the C's size/position, the opening direction "
    "and the gray shape/position all vary freely, with the mirror always "
    "landing in-bounds clear of the C (was a fixed 11x12 grid, ~8 "
    "configs)."
)

INVARIANTS = [
    "a red C-shape has exactly one open side",
    "one gray object sits just outside the open side",
    "the closed side opposite the opening is the mirror wall",
    "the output removes the original gray and paints its mirror image in-bounds",
]

OPENINGS = ("right", "left", "down", "up")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_C", "no_gray", "full_grid")
HELPFUL_TEXTURES = OPENINGS

_GRAY_SHAPES = [
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 1)],
    [(0, 0), (1, 0)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0), (1, 0), (2, 0)],
    [(0, 1), (1, 0), (1, 1)],
]

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "11..20"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..20"},
    "opening":        {"type": "str", "default": "rng helpful",
                       "valid": "right|left|down|up"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for opening",
                       "valid": "right|left|down|up|no_C|no_gray|full_grid"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: at least one color-2 (C-shape) cell and one color-5 (gray) cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_C", "no_gray", "full_grid"):
        return []
    errs = []
    c2 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 2)
    c5 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 5)
    if c2 == 0:
        errs.append("no color-2 (red C-shape) cells")
    if c5 == 0:
        errs.append("no color-5 (gray shape) cells")
    return errs


def _draw_c(g, r1, c1, r2, c2, opening):
    for c in range(c1, c2 + 1):
        if opening != "up":
            g[r1][c] = 2
        if opening != "down":
            g[r2][c] = 2
    for r in range(r1, r2 + 1):
        if opening != "left":
            g[r][c1] = 2
        if opening != "right":
            g[r][c2] = 2


def _mirror(cells, opening, r1, c1, r2, c2):
    out = []
    for r, c in cells:
        if opening == "right":
            out.append((r, 2 * c1 - c))
        elif opening == "left":
            out.append((r, 2 * c2 - c))
        elif opening == "down":
            out.append((2 * r1 - r, c))
        else:
            out.append((2 * r2 - r, c))
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    opening = (overrides.get("texture") if overrides.get("texture") in OPENINGS else None) or \
              overrides.get("opening") or \
              rng.choice(list(OPENINGS))

    if difficulty == "easy":
        hr, wr, cmax = (11, 13), (12, 14), 5
    elif difficulty == "hard":
        hr, wr, cmax = (15, 20), (16, 20), 6
    else:
        hr, wr, cmax = (12, 16), (13, 17), 6

    for _attempt in range(120):
        h = rng.randint(*hr); w = rng.randint(*wr)
        ch = rng.randint(4, min(cmax, h - 2)); cw = rng.randint(4, min(cmax, w - 2))
        r1 = rng.randint(1, h - ch - 1); c1 = rng.randint(1, w - cw - 1)
        r2 = r1 + ch - 1; c2 = c1 + cw - 1
        shape = rng.choice(_GRAY_SHAPES)
        gh = max(r for r, c in shape) + 1; gw = max(c for r, c in shape) + 1

        # Place the gray just outside the opening, spanning inside the C's
        # perpendicular extent.
        if opening == "right":
            gr = rng.randint(r1, max(r1, r2 - gh + 1)); gc = c2 + 1
        elif opening == "left":
            gr = rng.randint(r1, max(r1, r2 - gh + 1)); gc = c1 - gw
        elif opening == "down":
            gr = r2 + 1; gc = rng.randint(c1, max(c1, c2 - gw + 1))
        else:
            gr = r1 - gh; gc = rng.randint(c1, max(c1, c2 - gw + 1))

        gray = [(gr + dr, gc + dc) for dr, dc in shape]
        if not all(0 <= r < h and 0 <= c < w for r, c in gray):
            continue
        mirror = _mirror(gray, opening, r1, c1, r2, c2)
        if not all(0 <= r < h and 0 <= c < w for r, c in mirror):
            continue

        g = full_grid(h, w, 0)
        _draw_c(g, r1, c1, r2, c2, opening)
        # gray and its mirror must not land on the red C.
        if any(g[r][c] != 0 for r, c in gray) or any(g[r][c] != 0 for r, c in mirror):
            continue
        paint_at(g, gr, gc, shape, 5)
        return g

    # Fallback: the original known-valid fixed layout.
    g = full_grid(11, 12, 0)
    _draw_c(g, 3, 4, 7, 7, "right")
    paint_at(g, 4, 8, [(0, 0), (1, 0), (1, 1)], 5)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 12, 0)
    if name == "no_C":
        g[4][8] = 5
        return g
    if name == "no_gray":
        _draw_c(g, 3, 4, 7, 7, "right")
        return g
    if name == "full_grid":
        for r in range(11):
            for c in range(12):
                g[r][c] = 2
        return g
    return g
