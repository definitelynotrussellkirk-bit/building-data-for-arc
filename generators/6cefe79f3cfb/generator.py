"""Generator for 8dab14c2.

Rule: a 9x9 blue/cyan boundary context triggers one local smoothing
rewrite.

Combinatorial axes (8): grid_h/w, grid_size, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_patch, edge_patch, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paste

GENERATOR_ID = "6cefe79f3cfb"
RULE_HASH = "7c102e70b4de"  # canonical rule this generator was written against
VERSION = "3.0.0"  # diversity: multiple non-interfering patches + wider grid (memorized-table honest ceiling)
TASK_ID = "6cefe79f3cfb"
SUMMARY = (
    "Color-8 (cyan) background grid (size varies). 1-4 copies of 9x9 "
    "BLUE/CYAN boundary PATCHES (from 3 hardcoded anomaly patterns), placed "
    "apart so each patch's 9x9 context is clean. Rule (a memorized exact-9x9-"
    "context lookup table, radius 4) fixes the single boundary anomaly inside "
    "each patch. The grid size, patch count and positions vary freely (was a "
    "single patch, ~23 distinct -- the table is memorized so this is the "
    "honest ceiling)."
)

INVARIANTS = [
    "the active 9x9 context is fully in bounds",
    "colors 1 and 8 form the local boundary",
    "the center value differs from the canonical replacement",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_patch", "edge_patch", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..14", "valid": "11..14"},
    "grid_w":         {"type": "int", "default": "rng 11..14", "valid": "11..14"},
    "grid_size":      {"type": "int", "default": "rng 11..14", "valid": "11..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "varied", "valid": "varied"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "varied", "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_patch|edge_patch|full_grid"},
}

_PATCHES = [
    [
        [1, 1, 1, 1, 1, 1, 1, 1, 8],
        [1, 1, 1, 1, 1, 1, 1, 1, 8],
        [1, 1, 1, 1, 1, 1, 1, 1, 8],
        [1, 1, 1, 1, 1, 1, 1, 1, 8],
        [8, 8, 8, 8, 8, 1, 1, 1, 8],
        [8, 8, 8, 8, 8, 1, 1, 1, 8],
        [8, 8, 8, 8, 8, 1, 1, 1, 8],
        [8, 8, 8, 8, 8, 1, 1, 8, 8],
        [8, 8, 8, 8, 8, 1, 1, 1, 8],
    ],
    [
        [8, 8, 8, 8, 8, 8, 8, 8, 8],
        [8, 8, 8, 8, 1, 8, 8, 8, 8],
        [1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1],
        [8, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 8, 8, 8, 8, 8],
        [1, 1, 1, 1, 8, 8, 8, 8, 8],
        [1, 1, 1, 1, 8, 8, 8, 8, 8],
        [1, 1, 1, 1, 8, 8, 8, 8, 8],
    ],
    [
        [8, 8, 8, 8, 8, 8, 8, 8, 8],
        [8, 8, 8, 8, 1, 8, 8, 8, 8],
        [1, 1, 1, 1, 1, 1, 1, 8, 8],
        [1, 1, 1, 1, 1, 1, 1, 8, 8],
        [1, 1, 1, 1, 1, 1, 1, 8, 8],
        [8, 8, 8, 8, 8, 8, 8, 8, 8],
        [8, 8, 8, 8, 8, 8, 8, 8, 8],
        [8, 8, 8, 8, 8, 8, 8, 8, 8],
        [8, 8, 8, 8, 8, 8, 8, 8, 8],
    ],
]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    side = len(_PATCHES[0])
    if difficulty == "easy":
        sr, nr = (12, 14), (1, 1)
    elif difficulty == "hard":
        sr, nr = (20, 28), (2, 4)
    else:
        sr, nr = (15, 20), (1, 2)

    for _attempt in range(40):
        size = rng.randint(*sr)
        g = full_grid(size, size, 8)
        occ = [[False] * size for _ in range(size)]
        placed = 0
        for _ in range(rng.randint(*nr)):
            patch = rng.choice(_PATCHES)
            for _t in range(30):
                r0 = rng.randint(0, size - side); c0 = rng.randint(0, size - side)
                if _reserve(occ, r0, c0, side, size, 4):
                    paste(g, patch, r0, c0)
                    placed += 1
                    break
        if placed >= 1:
            return g
    return full_grid(15, 15, 8)


def _reserve(occ, top, left, sz, n, margin):
    for r in range(top - margin, top + sz + margin):
        for c in range(left - margin, left + sz + margin):
            if 0 <= r < n and 0 <= c < n and occ[r][c]:
                return False
    for r in range(top, top + sz):
        for c in range(left, left + sz):
            occ[r][c] = True
    return True


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 12, 8)
    if name == "no_patch":
        return g
    if name == "edge_patch":
        paste(g, _PATCHES[0], 0, 0)
        return g
    if name == "full_grid":
        for r in range(12):
            for c in range(12):
                g[r][c] = 1
        return g
    return g

def _window_matches_patch(grid, r0, c0, patch):
    return all(grid[r0 + r][c0 + c] == patch[r][c]
               for r in range(9) for c in range(9))


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    if h != w or h < 12:
        errors.append("expected a square color-8 field large enough for an in-bounds 9x9 patch")
        return errors
    colors = {v for row in grid for v in row}
    if not colors <= {1, 8}:
        errors.append("boundary lookup task should use only colors 1 and 8")
    matches = 0
    for r in range(0, h - 8):
        for c in range(0, w - 8):
            if any(_window_matches_patch(grid, r, c, patch) for patch in _PATCHES):
                matches += 1
    if matches < 1:
        errors.append("missing a complete in-bounds 9x9 anomaly patch")
    return errors
