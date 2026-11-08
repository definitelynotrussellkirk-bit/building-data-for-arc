"""Generator for arc_additional_puzzles_21_set14_bundle:M93.

Rule: each non-{0,8} SEED floods its 4-connected region of (0-or-same-color,
never crossing color-8) cells with the seed's color. In the canonical task the
color-8 cells form CLOSED RECTANGULAR ROOMS scattered across the grid; a room
with a seed inside has its interior flooded; a room with no seed stays empty.

The earlier generator drew a single PLUS divider (two full crossing color-8
lines -> 4 quadrants) with corner seeds — a different structure from the
canonical scattered rectangular rooms. This version places several separated
rectangular room boxes, some seeded (flooded) and some empty (negative).

Degenerates: no_seeds, no_walls, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ef65ec3491d7"
# 2.1.0: identity fix. A 3x3 room has a SINGLE interior cell, so seeding it and
# flooding just re-paints the seed -> no change. When every seeded room was 3x3
# the whole output equalled the input. Now force >=1 room to have a multi-cell
# interior and guarantee at least one such room is seeded, so a flood is visible.
VERSION = "2.1.0"  # scattered rectangular rooms (canonical) — was a single plus-divider into 4 quadrants
TASK_ID = "ef65ec3491d7"
SUMMARY = (
    "0-bg grid with several separated CLOSED RECTANGULAR ROOMS (color-8 "
    "outlines, sizes vary). Each room has 0 or 1 SEED (a non-{0,8} color) at an "
    "interior cell. Rule: every seed floods its room interior (4-connected "
    "0-cells bounded by the 8 walls) with its color; rooms without a seed stay "
    "empty. Room count/sizes/positions, seed colors, and which rooms are seeded "
    "all vary. (Was a single plus-divider with 4 corner seeds.)"
)

INVARIANTS = [
    "walls use color 8 forming closed rectangular rooms",
    "each room is separated so its flood cannot leak into another room or the exterior",
    "seeded rooms have exactly one seed (non-0,8) inside; >=1 room is seeded",
    "rooms without a seed stay empty (exercise the no-seed case)",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_seeds", "no_walls", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS
_SEED_COLORS = [1, 2, 3, 4, 5, 6, 7, 9]

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..18", "valid": "7..20"},
    "grid_w":         {"type": "int", "default": "rng 9..18", "valid": "7..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_rooms":        {"type": "int", "default": "rng 2..8 by difficulty", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "varies (one color per seeded room)", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "scattered_rooms", "valid": "scattered_rooms"},
    "n_distinct_colors":{"type": "int", "default": "varies", "valid": "1..8"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _place_room(g, occ, rng, h, w, min_inter=1):
    """Draw a closed rectangular color-8 room with a 1-cell margin from others.
    Returns the list of interior cells, or None. `min_inter` rejects rooms whose
    interior is smaller than that (use 2 to force a floodable multi-cell room)."""
    for _ in range(60):
        bh = rng.randint(3, 6); bw = rng.randint(3, 6)
        if bh > h or bw > w:
            continue
        if (bh - 2) * (bw - 2) < min_inter:
            continue
        r0 = rng.randint(0, h - bh); c0 = rng.randint(0, w - bw)
        if any(occ[r][c] for r in range(max(0, r0 - 1), min(h, r0 + bh + 1))
               for c in range(max(0, c0 - 1), min(w, c0 + bw + 1))):
            continue
        for c in range(c0, c0 + bw):
            g[r0][c] = 8; g[r0 + bh - 1][c] = 8
        for r in range(r0, r0 + bh):
            g[r][c0] = 8; g[r][c0 + bw - 1] = 8
        for r in range(r0, r0 + bh):
            for c in range(c0, c0 + bw):
                occ[r][c] = True
        interior = [(r, c) for r in range(r0 + 1, r0 + bh - 1)
                    for c in range(c0 + 1, c0 + bw - 1)]
        return interior
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 9, 11)
        n_rooms = ctx.draw_int("n_rooms", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 18); w = ctx.draw_int("grid_w", 14, 18)
        n_rooms = ctx.draw_int("n_rooms", 5, 8)
    else:
        h = ctx.draw_int("grid_h", 11, 15); w = ctx.draw_int("grid_w", 11, 15)
        n_rooms = ctx.draw_int("n_rooms", 3, 5)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    occ = [[False] * w for _ in range(h)]
    colors = list(_SEED_COLORS)
    rng.shuffle(colors)

    interiors = []
    for ridx in range(n_rooms):
        # force the FIRST room to have a multi-cell interior so a visible flood
        # is always possible (a 3x3 room's 1-cell interior can't flood)
        interior = _place_room(g, occ, rng, h, w,
                               min_inter=2 if ridx == 0 else 1)
        if interior:
            interiors.append(interior)

    # seed most rooms (each a distinct color); leave some empty as negatives.
    multi = [iv for iv in interiors if len(iv) >= 2]
    ci = 0
    seeded_multi = False
    for interior in interiors:
        if rng.random() < 0.72 and ci < len(colors):
            r, c = rng.choice(interior)
            g[r][c] = colors[ci]; ci += 1
            if len(interior) >= 2:
                seeded_multi = True
    # guarantee >=1 SEEDED multi-cell room so the flood changes the grid
    if not seeded_multi and multi and ci < len(colors):
        iv = multi[0]
        if all(g[r][c] == 0 for r, c in iv):
            r, c = rng.choice(iv)
            g[r][c] = colors[ci]; ci += 1
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """At least one seed (non-{0,8}) whose 4-connected region (0-or-same-colour,
    blocked by colour-8 walls) contains a 0-cell to flood, so the rule changes
    the grid (output != input)."""
    h, w = len(grid), len(grid[0])
    seeds = [(r, c) for r in range(h) for c in range(w)
             if grid[r][c] not in (0, 8)]
    if not seeds:
        return ["no seed -> nothing floods (identity)"]
    for sr, sc in seeds:
        col = grid[sr][sc]
        seen = {(sr, sc)}; stack = [(sr, sc)]; floods0 = False
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                        and grid[nr][nc] in (0, col)):
                    seen.add((nr, nc)); stack.append((nr, nc))
                    if grid[nr][nc] == 0:
                        floods0 = True
        if floods0:
            return []
    return ["no seed's region has a 0-cell to flood -> identity output"]


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 10, 0)
    if name == "no_seeds":
        # rooms but no seeds -> nothing floods, output == input
        for c in range(1, 5):
            g[1][c] = 8; g[4][c] = 8
        for r in range(1, 5):
            g[r][1] = 8; g[r][4] = 8
        return g
    if name == "no_walls":
        # seeds but no walls -> each floods the whole grid (ambiguous overlap)
        g[1][1] = 2; g[8][8] = 3
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(10):
                g[r][c] = 8
        return g
    return g
