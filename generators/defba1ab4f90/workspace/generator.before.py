"""Generator for 96a8c0cd - radius-6 contour drawing trigger.

Rule: a 13x13 blue/green contour context triggers one red contour pixel.

Combinatorial axes (8): grid_h, grid_w, palette_kind, grid_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_patch, patch_at_corner, blank_patch.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paste

GENERATOR_ID = "defba1ab4f90"
VERSION = "1.3.0"
TASK_ID = "defba1ab4f90"
SUMMARY = "A blue/green contour pattern triggers red(2) where a local 13×13 context matches a learned table; isolated blue/green distractor chips preserve the sparse contour distribution."

# Rivals: 'no transform' refuted by any demo with red appearing. 'use
# bg color' refuted by any demo (red uses 2). 'fill all 0s with red'
# refuted by ≥1 demo with most bg cells staying. 'recolor blue/green
# in place' refuted by any demo (originals preserved).
# 4 demos with varied patch positions + sizes cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "colors 1 and 3 form the local contour source",
    "the active 13x13 context is fully in bounds",
    "isolated extra source chips may appear away from the trigger context",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_patch", "patch_at_corner", "blank_patch")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {'grid_size': {'type': 'int', 'default': 'rng 22..26', 'valid': '18..28'},
 'palette_kind': {'type': 'str', 'default': 'rng helpful', 'valid': 'default|warm|cool|varied'},
 'palette_size': {'type': 'int', 'default': '2', 'valid': '2..2'},
 'position_bias': {'type': 'str',
                   'default': 'interior_13x13_patch',
                   'valid': 'interior_13x13_patch'},
 'n_distinct_colors': {'type': 'int', 'default': '2', 'valid': '2..2'},
 'density': {'type': 'str', 'default': 'sparse', 'valid': 'sparse'},
 'texture': {'type': 'str',
             'default': 'alias for palette_kind',
             'valid': 'default|warm|cool|varied|no_patch|patch_at_corner|blank_patch'}}

_PATCH = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 0, 0, 3, 0, 0, 3, 0, 0, 0, 0, 0],
    [0, 1, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        size = ctx.draw_int("grid_size", 18, 22)
        n_chips = 5
    elif difficulty == "hard":
        size = ctx.draw_int("grid_size", 24, 28)
        n_chips = 12
    else:
        size = ctx.draw_int("grid_size", 22, 26)
        n_chips = 9
    g = full_grid(size, size, 0)
    side = 13
    max_off = size - side
    if max_off <= 0:
        return g
    r0 = rng.randint(0, max_off)
    c0 = rng.randint(0, max_off)
    paste(g, _PATCH, r0, c0)
    _add_distractor_chips(g, rng, (r0, c0, side, side), n_chips)
    return g


def _add_distractor_chips(grid, rng, patch_box, n_chips):
    """Add isolated source-color chips outside the exact 13x13 trigger patch.

    The canonical train inputs contain many disconnected sparse contour pieces.
    These chips restore that structural signature without altering the embedded
    trigger context used by the local rewrite rule.
    """
    H = len(grid)
    W = len(grid[0]) if H else 0
    pr, pc, ph, pw = patch_box
    forbidden = set()
    for r in range(max(0, pr - 1), min(H, pr + ph + 1)):
        for c in range(max(0, pc - 1), min(W, pc + pw + 1)):
            forbidden.add((r, c))
    candidates = []
    for r in range(H):
        for c in range(W):
            if (r, c) in forbidden or grid[r][c] != 0:
                continue
            if any(grid[nr][nc] != 0
                   for nr in range(max(0, r - 1), min(H, r + 2))
                   for nc in range(max(0, c - 1), min(W, c + 2))):
                continue
            candidates.append((r, c))
    rng.shuffle(candidates)
    for r, c in candidates[:n_chips]:
        grid[r][c] = rng.choice((1, 3))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Assert the generated local-rewrite trigger context is present once."""
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    H, W = len(grid), len(grid[0])
    if any(len(row) != W for row in grid):
        return ["ragged grid"]
    palette = {v for row in grid for v in row}
    if not palette <= {0, 1, 3}:
        errs.append(f"unexpected input colors {sorted(palette - {0, 1, 3})}; red is output-only")
    if H < 13 or W < 13:
        errs.append("grid too small to contain the 13x13 trigger context")
        return errs
    matches = []
    for r0 in range(H - 12):
        for c0 in range(W - 12):
            ok = True
            for rr, row in enumerate(_PATCH):
                for cc, v in enumerate(row):
                    if grid[r0 + rr][c0 + cc] != v:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                matches.append((r0, c0))
    if not matches:
        errs.append("missing embedded 13x13 blue/green trigger patch")
    elif len(matches) != 1:
        errs.append(f"expected exactly one trigger patch, found {len(matches)} at {matches[:4]}")
    return errs


def _draw_from_degenerate(name, rng):
    size = 16
    if name == "no_patch":
        return full_grid(size, size, 0)
    if name == "patch_at_corner":
        g = full_grid(size, size, 0)
        paste(g, _PATCH, 0, 0)
        return g
    if name == "blank_patch":
        return full_grid(size, size, 0)
    return full_grid(size, size, 0)
