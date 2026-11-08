"""Generator for arc_puzzle_bank_eleventh21:E76 — keep unique smallest, erase rest.

Rule: among connected components, keep the uniquely smallest; erase larger ones.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_components, single_component, tied_smallest.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e5dcaca622f0"
VERSION = "2.0.0"  # the KEPT (smallest) object was ALWAYS a single cell (size 1) -> size-ranking discriminator trivial; canonical keeps a size-2. Now smallest is a random polyomino of size 1..3 and all distractors are strictly larger random polyominoes (distinct sizes), so the smallest is uniquely smallest and its kept shape varies.
TASK_ID = "e5dcaca622f0"

SUMMARY = "Keep only the unique smallest 4-connected nonzero component."

INVARIANTS = [
    "background is 0",
    "objects are separated 4-connected components",
    "one object is uniquely smallest",
    "all component sizes are distinct",
    "all larger objects are erased",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_components", "single_component", "tied_smallest")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "5..16"},
    "large_objects":  {"type": "int", "default": "rng 2..3", "valid": "1..8"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "2..8"},
    "position_bias":  {"type": "str", "default": "smallest_with_distractors",
                       "valid": "smallest_with_distractors"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "2..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_LARGE = [
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (0, 2)],
    [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)],
]


def _free(g, cells, top, left):
    h, w = len(g), len(g[0])
    coords = [(top + r, left + c) for r, c in cells]
    if any(r < 0 or c < 0 or r >= h or c >= w for r, c in coords):
        return False
    for r, c in coords:
        for rr, cc in [(r, c), (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]:
            if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0:
                return False
    return True


def _paint(g, cells, top, left, color):
    for r, c in cells:
        g[top + r][left + c] = color


def _poly(rng, k):
    """Random connected polyomino of k cells, normalized to (0,0)."""
    cells = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        cells.add((r + dr, c + dc))
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _place(g, rng, cells, color):
    """Try to place a polyomino at a free separated spot. Returns True/False."""
    h, w = len(g), len(g[0])
    mr = max(r for r, _ in cells)
    mc = max(c for _, c in cells)
    for _ in range(200):
        top = rng.randint(0, h - mr - 1)
        left = rng.randint(0, w - mc - 1)
        if _free(g, cells, top, left):
            _paint(g, cells, top, left, color)
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 9, 9)
        large = ctx.draw_int("large_objects", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 12, 15)
        large = ctx.draw_int("large_objects", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 12)
        large = ctx.draw_int("large_objects", 2, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    # The kept object: a small polyomino of size s0 (1..3), strictly the
    # smallest. Distractors get distinct sizes all > s0.
    s0 = rng.randint(1, 3)
    big_sizes = rng.sample(range(s0 + 1, s0 + 6), k=min(large, 5))
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], k=min(1 + len(big_sizes), 9))
    _place(g, rng, _poly(rng, s0), colors[0])
    for i, k in enumerate(big_sizes):
        _place(g, rng, _poly(rng, k), colors[(i + 1) % len(colors)])
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_components":
        # Empty grid — rule has no components to filter.
        return g
    if name == "single_component":
        # Only one component — rule's "uniquely smallest" is
        # trivially that component; output equals input.
        for r, c in [(2, 2), (2, 3), (3, 3)]: g[r][c] = 4
        return g
    if name == "tied_smallest":
        # Two equally-smallest components — rule's "uniquely
        # smallest" tie-break ambiguous; selection undefined.
        g[2][2] = 4
        g[5][7] = 6
        for r, c in [(7, 1), (7, 2), (8, 2)]: g[r][c] = 7
        return g
    return g
