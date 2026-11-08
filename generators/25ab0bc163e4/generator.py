"""Generator for additional_scaffolded:H3.

Rule: find the full-row or full-column color-9 axis; mirror every
non-{0,9} cell across it to fill the empty cells on the other side.

Combinatorial axes: grid size, the axis orientation/position, and the
blob(s) (shape / color / which side), each mirroring in-bounds.
Degenerates: no_axis, no_blob, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "25ab0bc163e4"
VERSION = "2.0.1"  # diversity: random axis (orient/pos) + blob (shape/color/side) + grid (was vertical axis + 1 fixed blob)
TASK_ID = "25ab0bc163e4"
SUMMARY = (
    "0-bg grid (size varies). A full COLOR-9 AXIS (a complete row or "
    "column of 9s) splits the grid; one or two small BLOBS (random "
    "shapes, a non-{0,9} color) sit entirely on one side of it, with "
    "their mirror positions empty. Rule: find the 9-axis and reflect "
    "every non-{0,9} cell across it, filling the empty mirror cells with "
    "the reflected color. The grid size, the axis orientation/position, "
    "and the blob shapes / colors / sides all vary freely, with every "
    "mirror landing in-bounds (was a fixed vertical axis + one fixed "
    "blob)."
)

INVARIANTS = [
    "exactly one full-row or full-column color-9 axis",
    "the blob(s) sit entirely on one side; their mirror cells start empty",
    "every mirror lands in-bounds clear of the axis",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_axis", "no_blob", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_axis|no_blob|full_grid"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly one full row or full column of color-9 (the axis)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    axis_rows = [r for r in range(h) if all(grid[r][c] == 9 for c in range(w))]
    axis_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    n_axes = len(axis_rows) + len(axis_cols)
    if n_axes == 0:
        return errors  # degenerate no_axis — allowed
    if n_axes != 1:
        errors.append(f"expected exactly 1 color-9 axis; found {n_axes} (rows={axis_rows} cols={axis_cols})")
    return errors


def _random_poly(rng, size, maxd):
    for _ in range(100):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            cells.add((r + dr, c + dc))
        mr = min(r for r, c in cells); mc = min(c for r, c in cells)
        norm = [(r - mr, c - mc) for r, c in cells]
        if max(r for r, c in norm) < maxd and max(c for r, c in norm) < maxd:
            return norm
    return [(0, 0), (1, 0), (1, 1)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, nb = (7, 9), (9, 11), 1
    elif difficulty == "hard":
        hr, wr, nb = (10, 16), (11, 16), 2
    else:
        hr, wr, nb = (8, 11), (9, 13), rng.randint(1, 2)

    for _attempt in range(60):
        h = rng.randint(*hr); w = rng.randint(*wr)
        vertical = rng.random() < 0.5
        g = full_grid(h, w, 0)
        if vertical:
            ac = rng.randint(3, w - 4)
            for r in range(h):
                g[r][ac] = 9
        else:
            ar = rng.randint(3, h - 4)
            for c in range(w):
                g[ar][c] = 9
        occ = [[g[r][c] != 0 for c in range(w)] for r in range(h)]

        def _mirror(r, c):
            return (r, 2 * ac - c) if vertical else (2 * ar - r, c)

        def _place(cells, color):
            bh = max(r for r, c in cells) + 1; bw = max(c for r, c in cells) + 1
            for _t in range(40):
                top = rng.randint(0, h - bh); left = rng.randint(0, w - bw)
                abs_cells = [(top + r, left + c) for r, c in cells]
                mir = [_mirror(r, c) for r, c in abs_cells]
                if any(occ[r][c] for r, c in abs_cells):
                    continue
                if any(not (0 <= mr < h and 0 <= mc < w) or occ[mr][mc] for mr, mc in mir):
                    continue
                # blob entirely on one side; mirror entirely on the other
                if vertical and not (all(c < ac for r, c in abs_cells) or all(c > ac for r, c in abs_cells)):
                    continue
                if not vertical and not (all(r < ar for r, c in abs_cells) or all(r > ar for r, c in abs_cells)):
                    continue
                for r, c in abs_cells:
                    g[r][c] = color; occ[r][c] = True
                for mr, mc in mir:
                    occ[mr][mc] = True            # reserve mirror so blobs don't collide
                return True
            return False

        cols = rng.sample([1, 2, 3, 4, 5, 6, 7, 8], 2)
        placed = 0
        for i in range(nb):
            if _place(_random_poly(rng, rng.randint(3, 5), 4), cols[i % len(cols)]):
                placed += 1
        if placed >= 1:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 10, 0)
    if name == "no_axis":
        g[1][2] = 2
        return g
    if name == "no_blob":
        for r in range(8):
            g[r][5] = 9
        return g
    if name == "full_grid":
        for r in range(8):
            for c in range(10):
                g[r][c] = 9
        return g
    return g
