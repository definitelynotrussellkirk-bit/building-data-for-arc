"""Generator for arc_additional_puzzle_bank_volume11:M73 — corner pairs expand into rectangle borders.

Rule: pairs of matching corner markers expand into same-colored
rectangle borders.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, single_marker, collinear_pair.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8c82d72dafe9"
VERSION = "2.0.1"
TASK_ID = "8c82d72dafe9"
SUMMARY = (
    "0-bg grid (h~10-18, w~10-18) with "
    "1-5 PAIRS OF MATCHING CORNER MARKERS: "
    "for each pair, pick a DISTINCT color "
    "from a shuffled palette {1..9}, pick "
    "an axis-aligned rectangle (r0, c0, "
    "r1, c1) with r1-r0 ≥ 2 AND c1-c0 ≥ "
    "2 (non-degenerate). PAINT only the "
    "TWO OPPOSITE DIAGONAL CORNERS at "
    "(r0, c0) and (r1, c1) with the "
    "pair's color. Pair rectangles do "
    "NOT overlap or touch (1-cell margin "
    "via _separate). Rule (EXPAND EACH "
    "PAIR'S TWO CORNERS INTO A FULL "
    "RECTANGLE BORDER IN THE SAME "
    "COLOR): for EACH color C with "
    "EXACTLY 2 cells at OPPOSITE "
    "DIAGONAL CORNERS of a non-"
    "degenerate rectangle: COMPUTE the "
    "bbox (r0, c0, r1, c1). PAINT every "
    "cell on the BBOX OUTLINE (top row "
    "r0, bottom row r1, left col c0, "
    "right col c1) with COLOR C. The "
    "two original corners stay color C "
    "(now part of the outline); the "
    "INTERIOR of the rectangle stays "
    "bg-0. Other pairs are expanded "
    "independently. Net: each pair's "
    "2 corners become a full hollow "
    "rectangular outline of the pair's "
    "color."
)

INVARIANTS = [
    "background is 0",
    "target colors appear exactly twice",
    "each marker pair forms opposite rectangle corners",
    "implied rectangles do not overlap",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "single_marker", "collinear_pair")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..15", "valid": "6..24"},
    "grid_w":         {"type": "int", "default": "rng 10..15", "valid": "6..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_pairs":        {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "= n_pairs", "valid": "1..5"},
    "position_bias":  {"type": "str", "default": "non_overlapping_corner_pairs",
                       "valid": "non_overlapping_corner_pairs"},
    "n_distinct_colors": {"type": "int", "default": "= n_pairs", "valid": "1..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_pairs|single_marker|collinear_pair"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; no non-bg color appears more than twice (corner pairs have exactly 2)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    counts: dict[int, int] = {}
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v != 0:
                counts[v] = counts.get(v, 0) + 1
    if not counts:
        return []  # no_pairs degenerate — allowed
    errs = []
    for color, cnt in counts.items():
        if cnt > 2:
            errs.append(f"color {color} appears {cnt} times (expected at most 2 for corner pairs)")
    return errs


def _separate(rect, rects):
    r0, c0, r1, c1 = rect
    for a0, b0, a1, b1 in rects:
        if not (r1 + 1 < a0 or a1 + 1 < r0 or c1 + 1 < b0 or b1 + 1 < c0):
            return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 10, 11)
        n_pairs = ctx.draw_int("n_pairs", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 18)
        w = ctx.draw_int("grid_w", 14, 18)
        n_pairs = ctx.draw_int("n_pairs", 3, 5)
    else:
        h = ctx.draw_int("grid_h", 10, 15)
        w = ctx.draw_int("grid_w", 10, 15)
        n_pairs = ctx.draw_int("n_pairs", 1, 3)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    colors = list(range(1, 10))
    rng.shuffle(colors)
    rects: list[tuple[int, int, int, int]] = []
    for color in colors:
        if len(rects) >= n_pairs:
            break
        for _ in range(120):
            r0 = rng.randint(0, h - 4)
            c0 = rng.randint(0, w - 4)
            r1 = rng.randint(r0 + 2, min(h - 1, r0 + 5))
            c1 = rng.randint(c0 + 2, min(w - 1, c0 + 5))
            rect = (r0, c0, r1, c1)
            if _separate(rect, rects):
                g[r0][c0] = color
                g[r1][c1] = color
                rects.append(rect)
                break
    if not rects:
        g[1][1] = 1
        g[4][5] = 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 12, 12
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # Empty grid — no marker pair to expand.
        return g
    if name == "single_marker":
        # Each color appears once — no pair, so no rectangle defined.
        g[2][2] = 4
        g[7][8] = 6
        return g
    if name == "collinear_pair":
        # Same-color cells on the same row — defines a line, not a
        # rectangle, so the rule's border-expansion is degenerate.
        g[3][1] = 4; g[3][8] = 4
        g[8][2] = 6; g[8][9] = 6
        return g
    return g
