"""Generator for arc_puzzle_bank_eighth21:H50.

Rule: the color-1 cell is the PIVOT. Each non-{0,1} payload cell is
replicated at its four 90-degree rotations about the pivot, all painted
in the FIRST payload cell's color, on a fresh grid (with the pivot kept).

This generator places a pivot and a payload in one quadrant, so the
rotations fill the other quadrants (output is a 4-fold pinwheel).

Combinatorial axes: grid size, pivot position, the payload offsets, and
the color.
Degenerates: no_pivot, no_payload, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3dcf9b8e9c1b"
VERSION = "2.0.1"  # diversity: random pivot + payload + color + grid (was fixed ~21)
TASK_ID = "3dcf9b8e9c1b"
SUMMARY = (
    "0-bg grid (size varies). A color-1 PIVOT and a payload of one color "
    "placed in a quadrant. Rule: replicate each payload cell at its four "
    "90-degree rotations about the pivot (in the payload color), producing "
    "a 4-fold pinwheel. The grid size, pivot position, payload offsets and "
    "color vary freely (was a fixed layout, ~21 distinct)."
)

INVARIANTS = [
    "exactly one color-1 pivot",
    "payload cells are a single non-{0,1} color in one quadrant of the pivot",
    "all four rotations of every payload cell land in-bounds",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pivot", "no_payload", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "9..20"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..22"},
    "n_payload":      {"type": "int", "default": "varies", "valid": "2..5"},
    "color":          {"type": "color", "default": "rng !{0,1}", "valid": "2..9"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "pivot_quadrant", "valid": "pivot_quadrant"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_pivot|no_payload|full_grid"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly one color-1 pivot cell and >=1 non-{0,1} payload cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    ones = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    payload = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 1)]
    if len(ones) != 1:
        errs.append(f"expected exactly 1 color-1 pivot, found {len(ones)}")
    if not payload:
        errs.append("no non-{0,1} payload cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)

    if difficulty == "easy":
        hr, wr, pr = (9, 11), (9, 12), (2, 3)
    elif difficulty == "hard":
        hr, wr, pr = (14, 20), (15, 22), (3, 5)
    else:
        hr, wr, pr = (11, 15), (12, 18), (2, 4)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        ar = rng.randint(3, h - 4); ac = rng.randint(3, w - 4)
        R = min(ar, h - 1 - ar, ac, w - 1 - ac)
        if R < 2:
            continue
        # payload offsets in the lower-right quadrant (dr>=1, dc>=0)
        cand = [(dr, dc) for dr in range(1, R + 1) for dc in range(0, R + 1)]
        n = rng.randint(*pr)
        offs = rng.sample(cand, min(n, len(cand)))
        color = rng.randint(2, 9)

        g = full_grid(h, w, 0)
        g[ar][ac] = 1
        for (dr, dc) in offs:
            g[ar + dr][ac + dc] = color
        return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 11, 0)
    g[5][5] = 1
    if name == "no_pivot":
        g2 = full_grid(11, 11, 0)
        g2[6][6] = 3
        return g2
    if name == "no_payload":
        return g
    if name == "full_grid":
        for r in range(11):
            for c in range(11):
                g[r][c] = 3
        g[5][5] = 1
        return g
    return g
