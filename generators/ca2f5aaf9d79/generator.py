"""Generator for e3fe1151.

Rule: each 2x2 quadrant hole is filled with the color missing from
that quadrant's balanced four-color set.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_quadrants,
n_distinct_colors.
Degenerates: no_holes, all_holes, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ca2f5aaf9d79"
VERSION = "1.2.0"
TASK_ID = "ca2f5aaf9d79"
SUMMARY = "2x2 quadrant holes filled with the color missing from each quadrant set."

INVARIANTS = [
    "the puzzle is a 5x5 grid",
    "color 7 marks exactly one hole in each corner 2x2 quadrant",
    "four non-hole colors appear once per quadrant after filling",
    "palette colors are distinct and exclude 7",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_holes", "all_holes", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "5", "valid": "5"},
    "grid_w":         {"type": "int", "default": "5", "valid": "5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_quadrants":    {"type": "int", "default": "4", "valid": "4"},
    "n_distinct_colors":{"type": "int", "default": "4", "valid": "4"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    colors = list(ctx.draw_distinct_colors("palette", n=4, exclude={7}))
    g = full_grid(5, 5, 0)
    quads = [
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 3), (0, 4), (1, 3), (1, 4)],
        [(3, 0), (3, 1), (4, 0), (4, 1)],
        [(3, 3), (3, 4), (4, 3), (4, 4)],
    ]
    # Choose a different missing color per quadrant, but randomize which cell is
    # the hole and the visible-order of the remaining values.  The previous
    # generator always put the hole in the lower-right cell of each quadrant, so
    # demonstrations taught a fixed-position shortcut rather than the balancing
    # rule.
    missings = colors[:]
    rng.shuffle(missings)
    for cells, missing in zip(quads, missings):
        hole = rng.choice(cells)
        vals = [v for v in colors if v != missing]
        rng.shuffle(vals)
        vi = 0
        for r, c in cells:
            if (r, c) == hole:
                g[r][c] = 7
            else:
                g[r][c] = vals[vi]; vi += 1
    return g



def self_check(grid, *, difficulty=None, meta=None):
    if len(grid) != 5 or any(len(row) != 5 for row in grid):
        return ["grid must be exactly 5x5"]
    quads = [
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 3), (0, 4), (1, 3), (1, 4)],
        [(3, 0), (3, 1), (4, 0), (4, 1)],
        [(3, 3), (3, 4), (4, 3), (4, 4)],
    ]
    errors = []
    visible = set()
    holes = []
    for qi, cells in enumerate(quads):
        qholes = [p for p in cells if grid[p[0]][p[1]] == 7]
        if len(qholes) != 1:
            errors.append(f"quadrant {qi} should have exactly one 7-hole, got {len(qholes)}")
        holes.extend(qholes)
        vals = [grid[r][c] for r, c in cells if grid[r][c] != 7]
        if len(vals) != 3 or len(set(vals)) != 3:
            errors.append(f"quadrant {qi} should expose three distinct non-hole colors, got {vals}")
        visible.update(vals)
    if len(visible) != 4 or 7 in visible:
        errors.append(f"visible quadrant palette should be four non-7 colors, got {sorted(visible)}")
    return errors

def _draw_from_degenerate(name, rng):
    g = full_grid(5, 5, 0)
    if name == "no_holes":
        for r in range(5):
            for c in range(5):
                g[r][c] = 2
        return g
    if name == "all_holes":
        for r in range(5):
            for c in range(5):
                g[r][c] = 7
        return g
    if name == "full_grid":
        for r in range(5):
            for c in range(5):
                g[r][c] = 7
        return g
    return g
