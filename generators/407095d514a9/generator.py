"""Generator for fe9372f3.

Rule: from the centroid of the color-2 core, shoot 4 CARDINAL rays
(skipping past the core, then a dashed 8/8/4 pattern out to the edge) and
4 DIAGONAL rays (solid color 1 out from the centre, stopping at a core
cell). The core stays color 2.

This generator emits a random connected color-2 core; the rule draws the
starburst.

Combinatorial axes: grid size, the core shape/size, and its position.
Degenerates: no_cross, single_cell, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "407095d514a9"
VERSION = "2.1.0"  # ensure random core contains its integer centroid; add self_check
TASK_ID = "407095d514a9"
SUMMARY = (
    "0-bg grid (size varies). A connected color-2 (red) CORE. Rule: from "
    "the core centroid, draw 4 cardinal rays (8/8/4 dashed pattern past the "
    "core to the edge) and 4 diagonal rays (solid color 1, stopping at the "
    "core). The grid size, core shape/size and position vary freely (was a "
    "fixed plus cross, ~17 distinct)."
)

INVARIANTS = [
    "the input is a single connected color-2 core",
    "cardinal rays paint an 8/8/4 dashed pattern from past the core to the edge",
    "diagonal rays paint solid color 1 outward until a core cell or the edge",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_cross", "single_cell", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "11..22"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "11..24"},
    "core_size":      {"type": "int", "default": "varies", "valid": "3..12"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "centred_core", "valid": "centred_core"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_cross|single_cell|full_grid"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _poly(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    return _norm(cells)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)

    if difficulty == "easy":
        hr, wr, sr = (11, 13), (11, 13), (3, 5)
    elif difficulty == "hard":
        hr, wr, sr = (16, 22), (17, 24), (6, 12)
    else:
        hr, wr, sr = (13, 17), (13, 18), (4, 8)

    for _attempt in range(100):
        shape = _poly(rng, rng.randint(*sr))
        sh = max(r for r, c in shape) + 1; sw = max(c for r, c in shape) + 1
        h = rng.randint(*hr); w = rng.randint(*wr)
        if sh + 2 > h or sw + 2 > w:
            continue
        # place the core roughly central (so the starburst has room all around)
        top = rng.randint(1, h - sh - 1); left = rng.randint(1, w - sw - 1)
        g = full_grid(h, w, 0)
        paint_at(g, top, left, shape, 2)
        twos = [(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v == 2]
        cr = sum(r for r, _ in twos) // len(twos)
        cc = sum(c for _, c in twos) // len(twos)
        if g[cr][cc] != 2:
            continue
        return g

    # Deterministic non-degenerate fallback: a centred plus contains its integer
    # centroid, so the Racket rule's ray origin is always anchored in the core.
    h = max(hr[0], 11); w = max(wr[0], 11)
    g = full_grid(h, w, 0)
    cr, cc = h // 2, w // 2
    for dr, dc in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:
        g[cr + dr][cc + dc] = 2
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 9, 0)
    if name == "no_cross":
        return g
    if name == "single_cell":
        g[4][4] = 2
        return g
    if name == "full_grid":
        for r in range(9):
            for c in range(9):
                g[r][c] = 2
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    from puzzle_generators.helpers.selfcheck import components
    errors = []
    twos = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    if len(twos) < 3:
        return ["color-2 core has fewer than 3 cells"]
    comps = components(grid, colors={2})
    if len(comps) != 1:
        errors.append(f"color-2 core is split into {len(comps)} components")
    cr = sum(r for r, _ in twos) // len(twos)
    cc = sum(c for _, c in twos) // len(twos)
    if grid[cr][cc] != 2:
        errors.append("integer centroid of color-2 core is not a core cell")
    return errors
