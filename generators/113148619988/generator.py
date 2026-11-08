"""Generator for arc_puzzle_bank_twentyfirst21:H146 — counted orbit around an anchor.

Rule: row 0 holds k color-1 cells (the rotation counter). The body
(rows 1..H-1, cols 0..W-2) contains exactly one color-9 anchor and
some non-{0,9} colored cells. Output is body-sized; the colored
cells are stamped at every 90° CCW rotation about the anchor for
turns = 0..k (so k+1 total orbits). Off-grid rotations are dropped.

Combinatorial axes (8): grid_h, grid_w, palette_kind, k_count,
n_orbit_cells, palette_size, anchor_pos, density, texture.
Degenerates: no_anchor, no_orbit_cells, k_too_large.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "113148619988"
VERSION = "1.2.1"  # +self_check
TASK_ID = "113148619988"
SUMMARY = (
    "Row 0 holds k color-1 markers (rotation count). Body (rows 1..H-1, "
    "cols 0..W-2) has one color-9 anchor + several non-{0,9} colored "
    "cells. Rule emits a (H-1) × (W-1) grid: anchor stays at 9, and "
    "each colored cell is stamped at every 90° CCW rotation about the "
    "anchor for turns = 0..k (k+1 stamps total). Off-bounds stamps drop."
)

# Rivals: 'output is input' refuted by any demo (output is smaller +
# new positions). 'rotate by fixed amount regardless of row 0'
# refuted by demos with k ∈ {0,1,2,3}. 'reflect instead of rotate'
# refuted by ≥1 demo with asymmetric orbit. 'use color-1 as anchor'
# refuted by any demo (9 is anchor). 3 demos with varied k cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "row 0 has between 0 and (W-1) color-1 cells",
    "body has exactly one color-9 anchor",
    "body has at least one non-{0,9} colored cell",
    "non-orbit body cells are background 0",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_anchor", "no_orbit_cells", "k_too_large")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..8", "valid": "4..12"},
    "grid_w":         {"type": "int", "default": "rng 5..8", "valid": "4..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "k_count":        {"type": "int", "default": "rng 0..3", "valid": "0..3"},
    "n_orbit_cells":  {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "rng 1..3", "valid": "1..6"},
    "anchor_pos":     {"type": "str", "default": "center",
                       "valid": "center|random"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        H = rng.randint(5, 6); W = rng.randint(5, 6)
        k = rng.randint(0, 1); n_orbit = rng.randint(1, 2)
    elif difficulty == "hard":
        H = rng.randint(8, 11); W = rng.randint(8, 11)
        k = rng.randint(2, 3); n_orbit = rng.randint(3, 5)
    else:
        H = rng.randint(6, 8); W = rng.randint(6, 8)
        k = rng.randint(1, 2); n_orbit = rng.randint(2, 3)
    body_h = H - 1
    body_w = W - 1
    g = full_grid(H, W, 0)
    # Place k color-1 markers in row 0, positions 0..W-2 (avoiding
    # the last col which is also stripped).
    if k > 0 and W - 1 >= k:
        k_positions = rng.sample(range(W - 1), k)
        for c in k_positions:
            g[0][c] = 1
    # Place 9-anchor in the body. Pick a position that lets at least
    # one orbit cell stay in bounds across rotations.
    anchor_r_body = rng.randint(1, body_h - 2)
    anchor_c_body = rng.randint(1, body_w - 2)
    g[anchor_r_body + 1][anchor_c_body] = 9
    # Place orbit cells in the body, non-9, non-anchor.
    palette_pool = [2, 3, 4, 5, 6, 7, 8]
    rng.shuffle(palette_pool)
    n_palette = max(1, min(len(palette_pool), n_orbit))
    palette = palette_pool[:n_palette]
    placed = 0
    attempts = 0
    while placed < n_orbit and attempts < 80:
        attempts += 1
        rr_body = rng.randint(0, body_h - 1)
        cc_body = rng.randint(0, body_w - 1)
        if (rr_body, cc_body) == (anchor_r_body, anchor_c_body):
            continue
        g_r = rr_body + 1
        g_c = cc_body
        if g[g_r][g_c] != 0:
            continue
        g[g_r][g_c] = rng.choice(palette)
        placed += 1
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Body has exactly one color-9 anchor AND at least one non-{0,9} cell."""
    if not grid or len(grid) < 2 or any(len(row) != len(grid[0]) for row in grid):
        return ["grid too small or not rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    anchor_cells = [(r, c) for r in range(1, h) for c in range(w) if grid[r][c] == 9]
    if len(anchor_cells) != 1:
        errors.append(f"expected exactly 1 color-9 anchor in body, got {len(anchor_cells)}")
    has_orbit = any(grid[r][c] not in (0, 9) for r in range(1, h) for c in range(w))
    if not has_orbit:
        errors.append("no non-{0,9} orbit cells in body")
    return errors


def _draw_from_degenerate(name, rng):
    g = full_grid(5, 5, 0)
    if name == "no_anchor":
        # No 9-anchor in body → rule can't pick anchor, undefined.
        g[0][0] = 1
        g[2][2] = 3
        return g
    if name == "no_orbit_cells":
        # Anchor exists but no colored cells → nothing to orbit.
        g[0][0] = 1
        g[2][2] = 9
        return g
    if name == "k_too_large":
        # Too many 1s in row 0 → all rotations probably go out of bounds.
        for c in range(4):
            g[0][c] = 1
        g[2][2] = 9
        g[1][1] = 4
        return g
    return g
