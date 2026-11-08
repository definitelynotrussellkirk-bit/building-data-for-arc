"""Generator for arc_puzzle_bank_21_set3:S3_E4 — recolor center of horizontal red triples.

Rule: each exact horizontal length-3 red line has its center cell recolored
blue. Vertical and longer red bars remain unchanged.

Combinatorial axes (8): grid_h, grid_w, palette_kind, triple_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_triples, only_triples, vertical_only.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.place import place_no_overlap

GENERATOR_ID = "427d6a7812dd"
VERSION = "2.0.1"
TASK_ID = "427d6a7812dd"
SUMMARY = (
    "0-bg grid (h~8-10, w~"
    "10-13) with 1-3 EXACT "
    "HORIZONTAL RED(2) "
    "TRIPLES (3-cell "
    "horizontal lines, all "
    "color 2) plus 1-2 "
    "OTHER red bars: "
    "length-2 horizontal "
    "(domino), length-4 "
    "horizontal, or "
    "length-3 VERTICAL — "
    "all in color 2 with 1-"
    "cell padding between "
    "them. Rule (RECOLOR "
    "CENTER OF EACH "
    "HORIZONTAL LENGTH-3 "
    "RED LINE TO BLUE): "
    "find every connected "
    "RED(2) COMPONENT. For "
    "EACH one that is "
    "EXACTLY a HORIZONTAL "
    "3-cell LINE (3 cells "
    "in the same row, "
    "consecutive columns)"
    ": identify its "
    "CENTER cell (middle "
    "of the 3). RECOLOR "
    "the center from 2 to "
    "BLUE (1). Endpoints "
    "stay red. Vertical "
    "and longer/shorter "
    "red bars are LEFT "
    "UNCHANGED. Net: each "
    "horizontal red "
    "triple gets a blue "
    "dot in its middle; "
    "all other red bars "
    "stay solid red."
)

INVARIANTS = [
    "background is 0",
    "all objects are red",
    "at least one object is an exact horizontal length-3 line",
    "vertical and longer red bars remain unchanged",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_triples", "only_triples", "vertical_only")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 10..13", "valid": "6..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "triple_count":   {"type": "int", "default": "rng 1..3", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "mixed_red_bars",
                       "valid": "mixed_red_bars"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_TRIPLE = [(0, 0), (0, 1), (0, 2)]
_OTHER = [
    [(0, 0), (0, 1)],
    [(0, 0), (0, 1), (0, 2), (0, 3)],
    [(0, 0), (1, 0), (2, 0)],
]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, all non-bg objects use color 2 (red)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    non_bg = set(grid[r][c] for r in range(h) for c in range(w)) - {0}
    if not non_bg:
        errs.append("no non-bg cells found (expected color-2 red objects)")
    if non_bg - {2}:
        errs.append(f"non-red, non-bg colors found: {non_bg - {2}}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 11)
        triple_count = ctx.draw_int("triple_count", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 12, 13)
        triple_count = ctx.draw_int("triple_count", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 10, 13)
        triple_count = ctx.draw_int("triple_count", 1, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    shapes = [_TRIPLE for _ in range(triple_count)]
    shapes.extend(rng.choice(_OTHER) for _ in range(rng.randint(1, 2)))
    rng.shuffle(shapes)
    for cells in shapes:
        if place_no_overlap(rng, g, cells, 2, padding=1, max_tries=400) is None:
            raise ValueError("could not place red bar")
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 12
    g = full_grid(h, w, 0)
    if name == "no_triples":
        # only non-triple bars → rule has no triples to operate on
        for (r, c) in [(2, 1), (2, 2)]: g[r][c] = 2  # length-2
        for (r, c) in [(5, 4), (5, 5), (5, 6), (5, 7)]: g[r][c] = 2  # length-4
        for (r, c) in [(2, 8), (3, 8), (4, 8)]: g[r][c] = 2  # vertical-3
        return g
    if name == "only_triples":
        # only triples → all centers recolor (no other-shape decoy)
        for (r, c) in [(2, 1), (2, 2), (2, 3)]: g[r][c] = 2
        for (r, c) in [(5, 5), (5, 6), (5, 7)]: g[r][c] = 2
        return g
    if name == "vertical_only":
        # all bars are vertical-3 → rule (which targets horizontal) has nothing
        for (r, c) in [(1, 2), (2, 2), (3, 2)]: g[r][c] = 2
        for (r, c) in [(1, 6), (2, 6), (3, 6)]: g[r][c] = 2
        for (r, c) in [(5, 9), (6, 9), (7, 9)]: g[r][c] = 2
        return g
    return g
