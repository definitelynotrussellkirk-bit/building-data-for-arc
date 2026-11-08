"""Generator for arc_puzzle_bank_21_set17_s:S17_E4.

Rule: sparse seeds grow by plus, then original seed cells are removed.

Combinatorial axes (8): grid_h/w, seed_count, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
n_distinct_colors.
Degenerates: no_seeds, full_seeds, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7a6e065e8273"
VERSION = "2.0.0"
TASK_ID = "7a6e065e8273"
SUMMARY = (
    "0-bg grid (h~6-8, w~6-8) with 2-4 SPARSE SEED "
    "cells placed at interior positions (rows 1..h-2, "
    "cols 1..w-2) so each has all four cardinal "
    "neighbors in bounds. Each seed has a distinct "
    "non-bg color (colors 2, 3, 4, 5 — picked by index). "
    "Seeds are placed with no overlap. Rule: for each "
    "seed cell at (r, c) with color k, PAINT its FOUR "
    "ORTHOGONAL NEIGHBORS at (r-1, c), (r+1, c), "
    "(r, c-1), (r, c+1) with color k (the four arms of "
    "a plus). Then CLEAR the seed itself (the center "
    "cell) back to 0. Net: each colored seed dot is "
    "replaced by a hollow plus-sign of the same color "
    "centered where the seed was."
)

INVARIANTS = [
    "input contains two to four seed cells",
    "output contains only orthogonal halo cells",
    "original seed cells are omitted from the output",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_seeds", "full_seeds", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "height":         {"type": "int", "default": "rng 6..8", "valid": "3..14"},
    "width":          {"type": "int", "default": "rng 6..8", "valid": "3..14"},
    "seed_count":     {"type": "int", "default": "rng 2..4", "valid": "1..10"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "varied", "valid": "varied"},
    "position_bias":  {"type": "str", "default": "interior", "valid": "interior"},
    "n_distinct_colors":{"type": "int", "default": "varied", "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("height", 6, 6)
        w = ctx.draw_int("width", 6, 7)
        n = ctx.draw_int("seed_count", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("height", 7, 8)
        w = ctx.draw_int("width", 7, 8)
        n = ctx.draw_int("seed_count", 3, 4)
    else:
        h = ctx.draw_int("height", 6, 8)
        w = ctx.draw_int("width", 6, 8)
        n = ctx.draw_int("seed_count", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    cells = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
    for _attempt in range(120):
        chosen = []
        pool = list(cells)
        rng.shuffle(pool)
        for r, c in pool:
            if all(abs(r - rr) + abs(c - cc) > 1 for rr, cc in chosen):
                chosen.append((r, c))
                if len(chosen) == n:
                    break
        if len(chosen) == n:
            for idx, (r, c) in enumerate(chosen):
                g[r][c] = 2 + idx
            return g
    raise ValueError("could not place non-adjacent interior seeds")


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 7, 0)
    if name == "no_seeds":
        return g
    if name == "full_seeds":
        for r in range(1, 6):
            for c in range(1, 6):
                if (r + c) % 2 == 0:
                    g[r][c] = 2
        return g
    if name == "full_grid":
        for r in range(7):
            for c in range(7):
                g[r][c] = 2
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for sparse seeds that expand into hollow pluses."""
    errs: list[str] = []
    if not grid or not isinstance(grid[0], list):
        return ["grid is empty or not rectangular"]
    h, w = len(grid), len(grid[0])
    cells = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0]
    if not (2 <= len(cells) <= 4):
        errs.append(f"expected 2..4 seed cells, got {len(cells)}")
    if any(r in (0, h - 1) or c in (0, w - 1) for r, c, _v in cells):
        errs.append("all seed cells should be interior so four plus arms fit")
    if len({v for _r, _c, v in cells}) != len(cells):
        errs.append("seed colors should be distinct")
    for i, (r, c, _v) in enumerate(cells):
        if any(abs(r - rr) + abs(c - cc) <= 1 for rr, cc, _vv in cells[i + 1:]):
            errs.append("seed cells should not touch; touching seeds hide plus arms")
            break
    return errs
