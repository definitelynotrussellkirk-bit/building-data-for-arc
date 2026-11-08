"""Generator for 342ae2ed -- connect same-color pairs with a diagonal.

Rule: background is 7. For each color that has exactly two objects, draw a
45-degree diagonal line (in that color) from the first object's near corner
toward the second, stopping at the second object. Endpoints are kept.

This generator places pairs of same-color markers at exact diagonal offsets
so each pair is connected by a clean 45-degree line.

Combinatorial axes: grid size, the number of color pairs, their diagonal
directions/lengths, colors and positions.
Degenerates: one_pair, no_pairs, single_marker.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6c08e545720f"
VERSION = "2.1.0"  # diversity: diagonal-offset same-color pairs -> connect (was fixed ~27)
TASK_ID = "6c08e545720f"
SUMMARY = (
    "7-bg grid (size varies) with pairs of same-color markers placed at exact "
    "diagonal offsets. Rule: for each color with two objects, draw a 45-degree "
    "diagonal connecting them. The grid size, pair count, diagonal "
    "directions/lengths, colors and positions vary freely (was a fixed setup, "
    "~27 distinct)."
)

INVARIANTS = [
    "background is 7; each used color appears as exactly two markers",
    "the two markers of a color are at a 45-degree diagonal offset",
    "the output draws the diagonal between each same-color pair",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("one_pair", "no_pairs", "single_marker")
HELPFUL_TEXTURES = PALETTE_KINDS

_COLORS = [1, 2, 3, 4, 5, 6, 8, 9]
_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..26"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..26"},
    "n_pairs":        {"type": "int", "default": "varies", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "1..4"},
    "position_bias":  {"type": "str", "default": "diagonal", "valid": "diagonal"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|one_pair|no_pairs|single_marker"},
}


def _reserve(occ, r0, c0, r1, c1, h, w, margin=1):
    rlo, rhi = min(r0, r1), max(r0, r1)
    clo, chi = min(c0, c1), max(c0, c1)
    for r in range(rlo - margin, rhi + margin + 1):
        for c in range(clo - margin, chi + margin + 1):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(rlo - margin, rhi + margin + 1):
        for c in range(clo - margin, chi + margin + 1):
            if 0 <= r < h and 0 <= c < w:
                occ[r][c] = True
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"])

    if difficulty == "easy":
        hr, wr, nr, lr = (12, 15), (12, 16), (1, 2), (3, 5)
    elif difficulty == "hard":
        hr, wr, nr, lr = (20, 26), (20, 26), (3, 4), (5, 9)
    else:
        hr, wr, nr, lr = (15, 20), (15, 21), (2, 3), (4, 7)

    for _attempt in range(120):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 7)
        occ = [[False] * w for _ in range(h)]
        npairs = rng.randint(*nr)
        cols = rng.sample(_COLORS, min(npairs, len(_COLORS)))
        placed = 0
        failed = False
        for color in cols:
            done = False
            for _t in range(120):
                dr, dc = rng.choice(_DIRS)
                L = rng.randint(*lr)
                r0 = rng.randint(0, h - 1); c0 = rng.randint(0, w - 1)
                r1 = r0 + L * dr; c1 = c0 + L * dc
                if not (0 <= r1 < h and 0 <= c1 < w):
                    continue
                if _reserve(occ, r0, c0, r1, c1, h, w):
                    g[r0][c0] = color; g[r1][c1] = color
                    placed += 1; done = True; break
            if not done:
                failed = True
                break
        if not failed and placed == len(cols):
            return g

    raise ValueError("could not realize all requested diagonal marker pairs")


def _draw_from_degenerate(name):
    h, w = 13, 14
    g = full_grid(h, w, 7)
    g[2][2] = 3; g[6][6] = 3
    if name == "one_pair":
        return g
    if name == "no_pairs":
        g2 = full_grid(h, w, 7); g2[2][2] = 3
        return g2
    if name == "single_marker":
        g[9][9] = 4
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(v not in range(10) for row in grid for v in row):
        errors.append("grid values must be digits 0..9")
    by_color = {}
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v != 7:
                by_color.setdefault(v, []).append((r, c))
    lo, hi = (1, 2) if difficulty == "easy" else ((3, 4) if difficulty == "hard" else (2, 3))
    if not (lo <= len(by_color) <= hi):
        errors.append(f"expected {lo}..{hi} diagonal marker pairs, got {len(by_color)}")
    for color, cells in by_color.items():
        if len(cells) != 2:
            errors.append(f"color {color} must appear exactly twice, got {len(cells)}")
            continue
        (r0, c0), (r1, c1) = cells
        if abs(r0 - r1) != abs(c0 - c1) or abs(r0 - r1) == 0:
            errors.append(f"color {color} endpoints must be on a nonzero 45-degree diagonal")
    return errors
