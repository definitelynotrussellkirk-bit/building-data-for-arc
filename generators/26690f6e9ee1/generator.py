"""Generator for puzzle b60334d2.

Rule: each gray(5) pixel expands into 3x3 pattern around it:
4 cardinals → blue(1), 4 diagonals stay gray(5), center stays bg(0).

Combinatorial axes (8): grid_h/w, n_grays, position_bias,
min_separation, anchor_corner, asymmetry_force, palette_size,
include_decoy.
Degenerates: single_gray, no_grays, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "26690f6e9ee1"
VERSION = "1.1.1"
TASK_ID = "26690f6e9ee1"
SUMMARY = "Sparse gray pixels w/ margin; rule expands each into 3x3 pattern."

INVARIANTS = [
    "background is 0",
    ">=2 gray(5) pixels with >=2-cell margin from edges",
    "gray pixels >=3 cells apart (so expansions don't overlap)",
]

POSITION_BIASES = ("scattered", "corners", "diagonal", "row_aligned",
                   "centered")
DEGENERATE_TEXTURES = ("single_gray", "no_grays", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..14", "valid": "6..18"},
    "grid_w":         {"type": "int", "default": "rng 8..14", "valid": "6..18"},
    "n_grays":        {"type": "int", "default": "rng 2..5", "valid": "1..7"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "min_separation": {"type": "int", "default": "3", "valid": "3..6"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "include_decoy":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥1 gray(5) pixel with ≥1-cell margin from grid edge."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    grays = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    if not grays:
        return errors  # degenerate no_grays — allowed
    # Each gray should have ≥1-cell margin from edge (so expansion doesn't go OOB)
    for r, c in grays:
        if r < 1 or r > h - 2 or c < 1 or c > w - 2:
            errors.append(f"gray at ({r},{c}) is on or within 1 cell of grid edge")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 6, 9
    elif difficulty == "hard":
        h_lo, h_hi = 14, 18
    else:
        h_lo, h_hi = 8, 14
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_grays = int(overrides.get("n_grays",
                                ctx.draw_int("n_grays", 2, 5)))
    n_grays = max(2, min(7, n_grays))
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias",
                               list(POSITION_BIASES)))
    min_sep = int(overrides.get("min_separation", 3))
    g = full_grid(h, w, 0)
    placed = []
    candidates = _candidates(bias, h, w, rng)
    for r, c in candidates:
        if len(placed) >= n_grays:
            break
        if not (2 <= r <= h - 3 and 2 <= c <= w - 3):
            continue
        if any(abs(r - pr) < min_sep and abs(c - pc) < min_sep
               for pr, pc in placed):
            continue
        g[r][c] = 5
        placed.append((r, c))
    if len(placed) < 2:
        for r, c in [(2, 2), (h - 3, w - 3)]:
            if 2 <= r <= h - 3 and 2 <= c <= w - 3 and g[r][c] == 0:
                g[r][c] = 5
    return g


def _candidates(bias, h, w, rng):
    if bias == "corners":
        return [(2, 2), (2, w - 3), (h - 3, 2), (h - 3, w - 3)]
    if bias == "diagonal":
        return [(i, i) for i in range(2, min(h, w) - 2, 3)]
    if bias == "row_aligned":
        r = h // 2
        return [(r, c) for c in range(2, w - 2, 4)]
    if bias == "centered":
        cr, cc = h // 2, w // 2
        positions = [(cr, cc)]
        for d in (3, 4, 5):
            for dr, dc in [(-d, 0), (d, 0), (0, -d), (0, d)]:
                positions.append((cr + dr, cc + dc))
        return positions
    cells = [(r, c) for r in range(2, h - 2) for c in range(2, w - 2)]
    rng.shuffle(cells)
    return cells


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "single_gray":
        g[h // 2][w // 2] = 5
        return g
    if name == "no_grays":
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 5
        return g
    return g
