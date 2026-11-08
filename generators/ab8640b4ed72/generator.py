"""Generator for arc_puzzle_bank_21_set20_bundle:easy_p07 — bridge midpoint of distance-2 same-color pair.

Rule: same-color endpoints separated by exactly one zero produce a
midpoint bridge in that color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, bridge_count, texture.
Degenerates: no_pairs, distance_one, distance_three.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ab8640b4ed72"
VERSION = "2.0.0"
TASK_ID = "ab8640b4ed72"
SUMMARY = (
    "0-bg grid (h~7-10, w~"
    "8-12) with 2-4 SAME-"
    "COLOR ENDPOINT TRIPLES "
    "— each TRIPLE consists "
    "of two cells of a "
    "DISTINCT non-0 color "
    "separated by EXACTLY "
    "ONE ZERO CELL between "
    "them, either "
    "HORIZONTAL (r, c), "
    "(r, c+1)=0, (r, c+2) "
    "or VERTICAL (r, c), "
    "(r+1, c)=0, (r+2, c). "
    "Triples don't overlap "
    "or touch each other "
    "(via 8-conn clearance "
    "check). Colors are "
    "distinct across "
    "triples. Rule (BRIDGE "
    "THE MIDPOINT OF EACH "
    "DISTANCE-2 SAME-COLOR "
    "PAIR): For each pair "
    "of same-color cells "
    "at axis-aligned "
    "distance 2 (one 0 "
    "between them): find "
    "the MIDPOINT cell "
    "(the 0-cell between)"
    " and PAINT it with "
    "the pair's color. "
    "The endpoints stay. "
    "Net: each distance-"
    "2 axis-aligned same-"
    "color pair becomes a "
    "solid 3-cell line."
)

INVARIANTS = [
    "background is 0",
    "each active pattern has two same-color cells separated by one zero",
    "patterns are separated to avoid accidental extra midpoint bridges",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "distance_one", "distance_three")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "bridge_count":   {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "= bridge_count", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "scattered_axis_distance_2",
                       "valid": "scattered_axis_distance_2"},
    "n_distinct_colors": {"type": "int", "default": "= bridge_count", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_pairs|distance_one|distance_three"},
}


def _clear_cells(grid, cells):
    h = len(grid)
    w = len(grid[0])
    for r, c in cells:
        for rr in range(max(0, r - 1), min(h, r + 2)):
            for cc in range(max(0, c - 1), min(w, c + 2)):
                if grid[rr][cc] != 0:
                    return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 10)
        bridge_count = ctx.draw_int("bridge_count", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 12, 16)
        bridge_count = ctx.draw_int("bridge_count", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 8, 12)
        bridge_count = ctx.draw_int("bridge_count", 2, 4)
    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], bridge_count)
    candidates = []
    for r in range(h):
        for c in range(w - 2):
            candidates.append(((r, c), (r, c + 1), (r, c + 2)))
    for r in range(h - 2):
        for c in range(w):
            candidates.append(((r, c), (r + 1, c), (r + 2, c)))
    rng.shuffle(candidates)
    placed = 0

    for a, mid, b in candidates:
        if placed >= bridge_count:
            break
        if not _clear_cells(grid, [a, mid, b]):
            continue
        color = colors[placed]
        grid[a[0]][a[1]] = color
        grid[b[0]][b[1]] = color
        placed += 1
    return grid


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        return g
    if name == "distance_one":
        # Adjacent same-color cells — rule's "one zero between"
        # precondition fails.
        g[2][2] = 4; g[2][3] = 4
        return g
    if name == "distance_three":
        # Pair separated by 2 zeros — rule's distance filter excludes.
        g[3][1] = 4; g[3][4] = 4
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Executable invariants for the distance-2 midpoint-bridge input."""
    errors = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    cells_by_color = {}
    for r, row in enumerate(grid):
        if len(row) != w:
            errors.append("grid rows must be rectangular")
            return errors
        for c, v in enumerate(row):
            if not isinstance(v, int) or not (0 <= v <= 9):
                errors.append(f"cell ({r},{c}) has invalid color {v!r}")
            if v != 0:
                cells_by_color.setdefault(v, []).append((r, c))
    if not cells_by_color:
        errors.append("default generation must contain at least one bridgeable color pair")
        return errors
    triples = []
    for color, cells in cells_by_color.items():
        if len(cells) != 2:
            errors.append(f"color {color} appears {len(cells)} times; expected exactly two endpoints")
            continue
        (r1, c1), (r2, c2) = sorted(cells)
        if r1 == r2 and abs(c1 - c2) == 2:
            mid = (r1, (c1 + c2) // 2)
        elif c1 == c2 and abs(r1 - r2) == 2:
            mid = ((r1 + r2) // 2, c1)
        else:
            errors.append(f"color {color} endpoints are not axis-aligned at distance 2: {cells}")
            continue
        if grid[mid[0]][mid[1]] != 0:
            errors.append(f"color {color} midpoint {mid} must be zero in the input")
        triples.append({(r1, c1), mid, (r2, c2)})
    # Triples should not overlap or touch in 8-neighborhood; otherwise the rule can
    # create accidental extra bridge cues not declared by the generator summary.
    for i in range(len(triples)):
        for j in range(i + 1, len(triples)):
            for r1, c1 in triples[i]:
                for r2, c2 in triples[j]:
                    if abs(r1 - r2) <= 1 and abs(c1 - c2) <= 1:
                        errors.append("bridge triples touch or overlap within 8-neighborhood")
                        return errors
    return errors

