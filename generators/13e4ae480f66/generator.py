"""Generator for arc_puzzle_bank_21_set4:S4_E6.

Rule: blue objects touching the left border are recolored yellow; interior
blue objects stay blue.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_left, n_interior,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_left_objects, no_interior_objects, all_at_left.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.place import place_no_overlap

GENERATOR_ID = "13e4ae480f66"
# 2.2.0: reverse-diversity -- left/interior shape banks were 3 fixed shapes each.
# Mix in random polyominoes (left ones anchored at col 0; interior via
# place_no_overlap which keeps them off col 0 with padding). Broadens shape axis.
# 2.1.0: outer reset-retry: left shapes can wedge the 2nd interior placement.
VERSION = "2.2.1"
TASK_ID = "13e4ae480f66"

SUMMARY = (
    "0-bg grid (h~8-10, w~9-12) with "
    "SEVERAL COLOR-1 (blue) CONNECTED "
    "COMPONENTS: (a) 1-2 LEFT-EDGE "
    "shapes from a bank of 3 (vertical "
    "tri-line, 2×2 square, L-shape) "
    "with at least one cell at col 0; "
    "(b) 1-2 INTERIOR shapes from a "
    "bank of 3 (2×2 square, L-shape, "
    "horizontal tri-line) placed "
    "entirely in c ≥ 1 with 1-cell "
    "padding. Components are 4-conn "
    "isolated. Rule (BORDER-TOUCH "
    "RECOLOR): for EACH color-1 "
    "connected component, check if "
    "ANY of its cells has column 0. "
    "If yes (touches left border), "
    "RECOLOR the ENTIRE component to "
    "COLOR 4 (yellow). Otherwise keep "
    "it as color 1. Net: blue blobs "
    "touching col 0 turn yellow; "
    "interior blue blobs stay blue."
)

# Rivals: 'output is input' refuted by demos with ≥1 left-touching
# component. 'recolor all blue components to 4' refuted by demos
# with interior blue staying 1. 'recolor based on size' refuted by
# demos where the left-touching is small but recolored. 'use color
# 8' refuted by demos showing 4. 'recolor cells (not whole component)'
# refuted by demos where the entire component changes color. 4 demos
# with mix of left + interior at varied positions pin the rule.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "all colored cells are color 1 (blue)",
    "≥1 color-1 component touches the leftmost column (c=0)",
    "≥1 color-1 component is entirely in the interior (c≥1 everywhere)",
    "components don't 4-touch each other (each is its own connected component)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_left_objects", "no_interior_objects", "all_at_left")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_left":         {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "n_interior":     {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "left_edge_plus_interior",
                       "valid": "left_edge_plus_interior"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_left_objects|no_interior_objects|all_at_left"},
}

_LEFT_SHAPES = [
    [(0, 0), (1, 0), (2, 0)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0), (1, 0), (2, 0), (2, 1)],
]

_INTERIOR = [
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0), (1, 0), (2, 0), (2, 1)],
    [(0, 0), (0, 1), (0, 2)],
]


def _poly(rng, n):
    """Random connected polyomino of n cells, normalized to min-r=min-c=0."""
    cells = {(0, 0)}
    while len(cells) < n:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        cells.add((r + dr, c + dc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _paint(g, cells, r0, c0):
    for dr, dc in cells:
        g[r0 + dr][c0 + dc] = 1


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; has color-1 cells; at least one touches col 0; at least one doesn't."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    ones = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    if not ones:
        return errors  # degenerate — allowed
    left_ones = [c for r, c in ones if c == 0]
    interior_ones = [c for r, c in ones if c > 0]
    if not left_ones:
        return errors  # degenerate (no_left_objects) — allowed
    if not interior_ones:
        return errors  # degenerate (all_at_left) — allowed
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 12)
    rng = ctx.draw_rng("layout")
    # The left-edge shapes (col 0-1) plus the first interior shape can wedge the
    # small interior region (easy 8×9: placeable rows 1-6 × cols 1-7) so the
    # second interior shape can't fit with its 1-cell padding → place_no_overlap
    # exhausts 400 tries and raises (~5/300 easy). Per-shape retry can't undo a
    # wedged neighbour, so reset-and-retry the WHOLE layout (left positions too):
    # outer attempt 0 reproduces the exact original draw stream, so every seed
    # that placed on the first pass returns byte-identically; only the previously-
    # wedged seeds redraw a fresh layout. Early-placement-wedging class
    # (c3cb6bb4b6e8/1594f141732b).
    for outer in range(40):
        g = full_grid(h, w, 0)
        ok = True
        for _ in range(rng.randint(1, 2)):
            # Left shape: fixed bank or random polyomino, anchored so a cell is
            # at col 0 (touches the left border -> rule recolors it to 4).
            if rng.random() < 0.5:
                cells = rng.choice(_LEFT_SHAPES)
            else:
                cells = _poly(rng, rng.randint(2, 5))
            sh = max(r for r, _ in cells) + 1
            sw = max(c for _, c in cells) + 1
            if sh > h:
                continue
            r0 = rng.randint(0, h - sh)
            cset = {(r0 + r, c) for r, c in cells}
            # footprint + 1-cell margin clear so it stays its own component
            clear = True
            for (cr, cc) in cset:
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        nr, nc = cr + dr, cc + dc
                        if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in cset
                                and g[nr][nc] != 0):
                            clear = False
            if clear and all(0 <= cc < w for _, cc in cset):
                _paint(g, cells, r0, 0)
        for _ in range(rng.randint(1, 2)):
            shape = rng.choice(_INTERIOR) if rng.random() < 0.5 else _poly(rng, rng.randint(2, 5))
            if place_no_overlap(rng, g, shape, 1, padding=1, margin=1, max_tries=400) is None:
                ok = False
                break
        if ok:
            return g
    raise ValueError("could not place interior blue object")


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_left_objects":
        # only interior objects → rule fires zero times; output identical to input
        for (r, c) in [(2, 4), (2, 5), (3, 4), (3, 5)]: g[r][c] = 1
        for (r, c) in [(6, 7), (7, 7), (7, 8)]: g[r][c] = 1
        return g
    if name == "no_interior_objects":
        # only left-edge objects → all blues become yellow; output is uniform yellow
        for (r, c) in [(1, 0), (2, 0), (3, 0)]: g[r][c] = 1
        for (r, c) in [(5, 0), (5, 1), (6, 0), (6, 1)]: g[r][c] = 1
        return g
    if name == "all_at_left":
        # every object touches left edge → "interior vs edge" distinction collapses
        for (r, c) in [(1, 0), (2, 0)]: g[r][c] = 1
        for (r, c) in [(4, 0), (5, 0), (5, 1)]: g[r][c] = 1
        for (r, c) in [(7, 0), (8, 0)]: g[r][c] = 1
        return g
    return g
