"""Generator for e2092e0c.

Rule: a 5x5 cue window inside a dense noisy 15x15 field triggers a local
draw of color 5.

Combinatorial axes (8): grid_h/w, grid_size, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_patch, edge_patch, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paste

GENERATOR_ID = "83edd318e70a"
VERSION = "1.3.0"  # restore dense 15x15 ARC-like noise around the cue patch
TASK_ID = "83edd318e70a"
SUMMARY = (
    "Dense 15×15 noisy field with one embedded 5×5 cue window of mixed colors; "
    "the rule's local-rewrite table converts certain matching local-bg(0) cells "
    "near that cue to color 5."
)

# Rivals: 'recolor every 0 cell to 5' refuted by ≥1 demo where some
# 0 cells stay 0. 'use cue cell colors for recolor' refuted by any
# demo (recolor is 5). 'recolor cue cells themselves' refuted by ≥1
# demo where cue colors stay. 'paint anywhere on grid' refuted by ≥2
# demos where recolor stays near the cue's 5×5 window.
# 4 demos with varied cue positions cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "0 is the modal background but the canvas is dense/noisy like the canonical task",
    "the cue context is fully in bounds",
    "at least one full 5x5 cue patch is present",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_patch", "edge_patch", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "15", "valid": "13..17"},
    "grid_w":         {"type": "int", "default": "15", "valid": "13..17"},
    "grid_size":      {"type": "int", "default": "15", "valid": "13..17"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "varied", "valid": "varied"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "varied", "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_PATCHES = [
    [
        [0, 0, 0, 0, 0],
        [0, 8, 0, 0, 0],
        [0, 1, 0, 3, 7],
        [2, 0, 9, 3, 4],
        [0, 8, 0, 0, 0],
    ],
    [
        [0, 0, 0, 0, 4],
        [8, 0, 0, 0, 7],
        [1, 0, 3, 7, 0],
        [0, 9, 3, 4, 0],
        [8, 0, 0, 0, 4],
    ],
    [
        [0, 0, 4, 9, 0],
        [0, 0, 7, 2, 2],
        [3, 7, 0, 0, 0],
        [3, 4, 0, 0, 1],
        [0, 0, 4, 0, 0],
    ],
]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        size = int(overrides.get("grid_size", ctx.draw_int("grid_size", 15, 15)))
        n_patches = 1
        noise_p = 0.34
    elif difficulty == "hard":
        size = int(overrides.get("grid_size", ctx.draw_int("grid_size", 15, 16)))
        n_patches = int(overrides.get("n_patches", 1))
        noise_p = 0.42
    else:
        size = int(overrides.get("grid_size", ctx.draw_int("grid_size", 15, 15)))
        n_patches = int(overrides.get("n_patches", 1))
        noise_p = 0.38
    size = max(13, min(size, 17))
    g = _draw_noisy_canvas(size, rng, noise_p)
    placed_corners = []
    for _ in range(n_patches):
        patch = [row[:] for row in rng.choice(_PATCHES)]
        for _ in range(40):
            r0 = rng.randint(0, size - 5)
            c0 = rng.randint(0, size - 5)
            if any(abs(r0 - pr) < 6 and abs(c0 - pc) < 6
                   for pr, pc in placed_corners):
                continue
            paste(g, patch, r0, c0)
            placed_corners.append((r0, c0))
            break
    return g


def _draw_noisy_canvas(size, rng, nonzero_p):
    """Canonical task is not a sparse zero field: it is salt-and-pepper 15x15
    noise with 0 as modal background.  Draw that first, then paste the cue so
    the exact local-rewrite trigger remains present."""
    g = full_grid(size, size, 0)
    colors = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    for r in range(size):
        for c in range(size):
            if rng.random() < nonzero_p:
                g[r][c] = rng.choice(colors)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 8, 0)
    if name == "no_patch":
        return g
    if name == "edge_patch":
        paste(g, _PATCHES[0], 0, 0)
        return g
    if name == "full_grid":
        for r in range(8):
            for c in range(8):
                g[r][c] = 5
        return g


def _matches_patch(grid, r0, c0):
    h, w = len(grid), len(grid[0]) if grid else 0
    if r0 < 0 or c0 < 0 or r0 + 5 > h or c0 + 5 > w:
        return False
    window = [row[c0:c0 + 5] for row in grid[r0:r0 + 5]]
    return any(window == patch for patch in _PATCHES)


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if h != w:
        msgs.append("cue-window tasks should use square grids")
    if not (13 <= h <= 17):
        msgs.append("normal instances should stay near the canonical 15x15 size")
    found = [(r, c) for r in range(max(0, h - 4)) for c in range(max(0, w - 4))
             if _matches_patch(grid, r, c)]
    if not found:
        msgs.append("normal instance should contain at least one complete cue patch")
    # Normal generation should be a dense noisy field, not just a sparse cue patch.
    vals = {v for row in grid for v in row}
    if vals <= {0} or vals <= {5}:
        msgs.append("normal instance should contain cue colors, not a constant field")
    nonzero = sum(1 for row in grid for v in row if v != 0)
    if nonzero < max(40, h * w // 4):
        msgs.append("normal instance is too sparse for the canonical noisy-field task")
    return msgs
