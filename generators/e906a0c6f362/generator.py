"""Generator for puzzle 782b5218.

Rule: input has a 'primary' color (first non-bg, non-red cell in
row-major scan) and red(2) markers in each column. Output paints each
column: above red → 0, at red → 2, below red → primary.

Combinatorial axes (8): grid_h/w, primary_color, primary_position,
red_distribution, red_min_row, red_max_row, anchor_corner,
asymmetry_force.
Degenerates: no_primary, no_reds, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e906a0c6f362"
VERSION = "3.0.0"  # was a CLEAN single-red-per-column field (min==max -> the multi-red BAND branch never exercised, 0/24 multi-red cols) and not the noisy {0,primary,2} field the canonical uses. Now a noisy multi-red field matching canonical
TASK_ID = "e906a0c6f362"
SUMMARY = (
    "Noisy field of {0, a single primary colour, red(2)} (like the canonical). "
    "Rule: primary = first non-0/non-2 cell (row-major). For each column: rows "
    "ABOVE its first red -> 0; rows from first..last red keep the 2s (other "
    "cells -> 0); rows BELOW its last red -> primary. Columns have varied "
    "multi-red bands so the band-preservation branch is exercised; primary "
    "colour, densities and grid size all vary."
)

INVARIANTS = [
    "background is 0; only colours present are {0, primary, 2}",
    ">=1 primary cell exists (so the row-major scan finds the primary colour)",
    "every column has >=1 red(2) cell (else that column collapses to 0)",
    "primary != 2 and != 0",
    "many columns have >1 red so first<last (a real band to preserve)",
]

DEGENERATE_TEXTURES = ("no_primary", "no_reds", "full_grid")
HELPFUL_TEXTURES = ("sparse", "medium", "dense")

AXES = {
    "grid_h":     {"type": "int", "default": "rng 8..18 by diff", "valid": "6..18"},
    "grid_w":     {"type": "int", "default": "rng 6..16 by diff", "valid": "4..16"},
    "primary":    {"type": "color", "default": "rng (!=0,2)", "valid": "1..9 (!=2)"},
    "red_pct":    {"type": "int", "default": "rng 15..32", "valid": "8..40"},
    "primary_pct":{"type": "int", "default": "rng 20..45", "valid": "10..55"},
    "texture":    {"type": "str", "default": "alias for density",
                   "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 9); w = ctx.draw_int("grid_w", 6, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 18); w = ctx.draw_int("grid_w", 12, 16)
    else:
        h = ctx.draw_int("grid_h", 9, 14); w = ctx.draw_int("grid_w", 8, 12)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    primary = int(overrides.get("primary", ctx.draw_color("primary", exclude={0, 2})))
    red_p = int(overrides.get("red_pct", ctx.draw_int("red_pct", 15, 32))) / 100.0
    prim_p = int(overrides.get("primary_pct", ctx.draw_int("primary_pct", 20, 45))) / 100.0

    g = full_grid(h, w, 0)
    for r in range(h):
        for c in range(w):
            x = rng.random()
            if x < red_p:
                g[r][c] = 2
            elif x < red_p + prim_p:
                g[r][c] = primary
    # every column needs >=1 red; bias toward >=2 in some columns so bands exist
    for c in range(w):
        reds = [r for r in range(h) if g[r][c] == 2]
        if not reds:
            g[rng.randint(0, h - 1)][c] = 2
        elif len(reds) == 1 and rng.random() < 0.5:
            others = [r for r in range(h) if r != reds[0]]
            g[rng.choice(others)][c] = 2          # make a band in ~half of single-red cols

    # The rule has a distinct first-red/last-red band branch.  Random density alone
    # occasionally produced an all-single-red example, so the branch was not
    # exercised despite the generator contract saying multi-red bands are present.
    min_multi = max(1, w // 4)
    multi_cols = [c for c in range(w) if sum(1 for r in range(h) if g[r][c] == 2) >= 2]
    if len(multi_cols) < min_multi:
        for c in [c for c in range(w) if c not in multi_cols]:
            reds = [r for r in range(h) if g[r][c] == 2]
            choices = [r for r in range(h) if r not in reds]
            if choices:
                g[rng.choice(choices)][c] = 2
                multi_cols.append(c)
                if len(multi_cols) >= min_multi:
                    break

    # guarantee >=1 primary cell for the row-major primary scan without deleting a
    # column's only red marker.
    if not any(g[r][c] == primary for r in range(h) for c in range(w)):
        candidates = [(r, c) for r in range(h) for c in range(w) if g[r][c] != 2]
        if candidates:
            r, c = rng.choice(candidates)
            g[r][c] = primary
        else:
            g[0][0] = primary
            if h > 1:
                g[1][0] = 2
    return g


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "no_primary":
        # Reds but no primary color → rule has no primary to use
        for c in range(w):
            g[h // 2][c] = 2
        return g
    if name == "no_reds":
        # Primary but no reds → rule's column rules don't fire
        g[0][0] = 3
        return g
    if name == "full_grid":
        primary = 4
        for r in range(h):
            for c in range(w):
                g[r][c] = primary if (r + c) % 2 == 0 else 2
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for first-red/last-red column-band inputs."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs: list[str] = []
    colors = {v for row in grid for v in row}
    primaries = sorted(colors - {0, 2})
    if len(primaries) != 1:
        errs.append(f"expected exactly one primary color, got {primaries}")
    for c in range(w):
        if not any(grid[r][c] == 2 for r in range(h)):
            errs.append(f"column {c} has no red marker")
    multi_cols = sum(1 for c in range(w) if sum(1 for r in range(h) if grid[r][c] == 2) >= 2)
    min_multi = max(1, w // 4)
    if multi_cols < min_multi:
        errs.append(f"only {multi_cols} multi-red columns; expected at least {min_multi}")
    return errs
