"""Generator for arc_puzzle_bank_21_set17_bundle:hard_p01 — laser-bounce trail.

Rule: a source cell on the border (color in non-{0, 1, 2, 5}) emits a beam
inward. Mirror 1 is /, mirror 2 is \\, color 5 is wall. The beam paints 0-cells
along its path with the source color until it hits a wall or exits.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, n_mirrors, n_walls, texture.
Degenerates: no_source, no_mirrors, source_in_corner.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e005c30bc59a"
VERSION = "2.0.0"
TASK_ID = "e005c30bc59a"

SUMMARY = (
    "0-bg grid (h~9-12, w~"
    "10-13) with: (a) ONE "
    "SOURCE CELL on the GRID "
    "BORDER in a color from "
    "{3, 4, 6, 7, 8, 9}; (b) "
    "1-4 MIRROR cells inside "
    "the grid (not on border) "
    "in COLOR 1 (forward "
    "slash /, reflects beam) "
    "or COLOR 2 (back slash "
    "\\\\, reflects beam); (c) "
    "0-2 WALL cells in COLOR "
    "5 (block beam). Mirrors "
    "and walls placed at "
    "distinct interior "
    "positions. Rule (LASER "
    "BOUNCE & PAINT TRAIL IN "
    "SOURCE COLOR): identify "
    "the BORDER SOURCE and "
    "its INWARD DIRECTION. "
    "EMIT a beam from the "
    "source inward. STEP "
    "through cells: if 1 "
    "(slash /), REFLECT (right→"
    "up, up→right, left→down, "
    "down→left); if 2 "
    "(backslash \\\\), REFLECT "
    "(right→down, down→right, "
    "left→up, up→left); if 5 "
    "(wall), STOP. PAINT each "
    "0-cell along the path "
    "with the SOURCE COLOR. "
    "Mirrors, walls, and "
    "source stay. Net: laser "
    "trail in source color "
    "from border, reflecting "
    "off mirrors, stopped by "
    "walls."
)

# Rivals: 'straight beam ignore mirrors' refuted by ≥1 demo where the
# beam visibly reflects. 'mirror=1 and mirror=2 same direction' refuted
# by ≥2 demos contrasting them. 'beam crosses walls' refuted by ≥1
# demo where the beam stops at a wall. 'paint with mirror color'
# refuted by any demo (always source color). 'paint entire grid'
# refuted by any sparse path demo.
# 4 demos with varied mirror counts + at least one wall stop case.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly one source cell on the grid border in a non-{0, 1, 2, 5} color",
    "1-3 mirror cells (color 1 or 2) inside the grid (not on border)",
    "0-2 wall cells (color 5) sparsely placed",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_source", "no_mirrors", "source_in_corner")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..15"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_mirrors":      {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "n_walls":        {"type": "int", "default": "rng 0..2", "valid": "0..4"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "border_source_inner_mirrors",
                       "valid": "border_source_inner_mirrors"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
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
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 11)
        n_mirrors = ctx.draw_int("n_mirrors", 1, 2)
        n_walls = ctx.draw_int("n_walls", 0, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 14)
        w = ctx.draw_int("grid_w", 13, 15)
        n_mirrors = ctx.draw_int("n_mirrors", 3, 4)
        n_walls = ctx.draw_int("n_walls", 2, 4)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 10, 13)
        n_mirrors = ctx.draw_int("n_mirrors", 1, 4)
        n_walls = ctx.draw_int("n_walls", 0, 2)
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    source_color = rng.choice([3, 4, 6, 7, 8, 9])
    border = []
    for c in range(w): border.extend([(0, c), (h - 1, c)])
    for r in range(1, h - 1): border.extend([(r, 0), (r, w - 1)])
    sr, sc = rng.choice(border)
    g[sr][sc] = source_color
    for _ in range(n_mirrors):
        for _t in range(40):
            r = rng.randint(1, h - 2); c = rng.randint(1, w - 2)
            if g[r][c] != 0: continue
            g[r][c] = rng.choice([1, 2])
            break
    for _ in range(n_walls):
        for _t in range(40):
            r = rng.randint(1, h - 2); c = rng.randint(1, w - 2)
            if g[r][c] != 0: continue
            g[r][c] = 5
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    g = full_grid(h, w, 0)
    if name == "no_source":
        # Mirrors and walls but no border source — rule has no beam
        # to launch.
        g[3][4] = 1; g[5][6] = 2
        g[7][3] = 5
        return g
    if name == "no_mirrors":
        # Source on border but no mirrors — beam travels straight
        # until it exits or hits a wall; rule's reflection step never
        # fires.
        g[0][5] = 4
        g[5][3] = 5
        return g
    if name == "source_in_corner":
        # Source at a corner — beam direction is ambiguous (corner has
        # two valid inward directions, no canonical pick).
        g[0][0] = 4
        g[3][3] = 1
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    issues = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    bad = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row)
           if v not in range(10)]
    if bad:
        issues.append("grid contains non-digit colors")
    border_sources = []
    mirrors = []
    walls = []
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            on_border = r in (0, h - 1) or c in (0, w - 1)
            if v in (3, 4, 6, 7, 8, 9) and on_border:
                border_sources.append((r, c, v))
            if v in (1, 2):
                mirrors.append((r, c))
                if on_border:
                    issues.append("mirror on border")
            if v == 5:
                walls.append((r, c))
                if on_border:
                    issues.append("wall on border")
    if len(border_sources) != 1:
        issues.append(f"expected exactly one border source, found {len(border_sources)}")
    if not (1 <= len(mirrors) <= 4):
        issues.append(f"expected 1..4 interior mirrors, found {len(mirrors)}")
    if len(walls) > 4:
        issues.append(f"expected at most 4 walls, found {len(walls)}")
    return issues
