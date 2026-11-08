"""Generator for arc_additional_puzzle_bank_volume8:M52 — paint rect borders defined by marker pairs.

Rule: for each of color 2 and color 1, if there are exactly 2 cells
of that color in the input, find the bbox of those 2 cells and paint
its border (perimeter cells) with the corresponding output color:
2 → 3 paints the perimeter, 1 → 8 paints the perimeter. Cells inside
the bbox interior (not on the perimeter) remain unchanged. Other
colors are preserved.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d414585aa873"
VERSION = "2.0.0"  # rewrite — old generator hardcoded everything
TASK_ID = "d414585aa873"
SUMMARY = (
    "0-bg grid with exactly two color-2 cells at diagonal corners of "
    "a non-degenerate rectangle, exactly two color-1 cells at diagonal "
    "corners of another non-degenerate rectangle, and 0..2 decoration "
    "cells in colors not in {0, 1, 2, 3, 8}. Rule: for color 2, paint "
    "the bbox border (perimeter) of its two cells with color 3. For "
    "color 1, paint the bbox border with color 8. Markers themselves "
    "become part of the painted perimeter; interior bbox cells stay "
    "unchanged (0 or decoration color). Other cells preserved."
)

# Rivals: 'output is input' refuted by demos with non-degenerate
# rectangles. 'fill the rect interior too' refuted by demos showing
# only the border. 'use marker color for the border' refuted by demos
# showing color 3 / 8. 'use color 8 for both 1s and 2s' refuted by
# demos. 'paint only color 1 (skip 2)' refuted by demos. 'paint only
# when count == 1' refuted (count must be 2). 4 demos with varied
# rect sizes and positions pin the rule.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly two color-2 cells at strictly different rows AND different columns",
    "exactly two color-1 cells at strictly different rows AND different columns",
    "the two rectangles don't share corners or overlap markers",
    "rectangle dimensions are ≥3×3 (so borders have a visible interior)",
    "0..2 decoration cells in colors NOT in {0, 1, 2, 3, 8} so output colors are unambiguous",
]

PALETTE_KINDS = ("default", "wide_separation", "tight_rects", "varied_corners")
DEGENERATE_TEXTURES = ("only_one_cell", "three_cells", "cells_aligned")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "rng 11..14", "valid": "9..18"},
    "rect_min_h":     {"type": "int", "default": "rng 3..4", "valid": "3..6"},
    "rect_min_w":     {"type": "int", "default": "rng 3..4", "valid": "3..6"},
    "n_decor":        {"type": "int", "default": "rng 0..2", "valid": "0..3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..6"},
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
        w = ctx.draw_int("grid_w", 10, 12)
        n_decor = ctx.draw_int("n_decor", 0, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 16)
        w = ctx.draw_int("grid_w", 14, 18)
        n_decor = ctx.draw_int("n_decor", 1, 3)
    else:
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 12, 14)
        n_decor = ctx.draw_int("n_decor", 0, 2)
    rng = ctx.draw_rng("layout")
    # Placing two non-overlapping non-degenerate rectangles is a constrained
    # problem on the smaller/easy boards.  The old code ignored a failed second
    # placement and emitted examples with only one color-1 marker.  Retry the
    # whole layout so default generation fails closed instead of silently
    # changing the rule.
    for _attempt in range(120):
        g = full_grid(h, w, 0)
        placed_rects = []  # (r1, c1, r2, c2)

        def _place_pair(color):
            for _ in range(90):
                r1 = rng.randint(0, h - 4)
                r2 = rng.randint(r1 + 2, h - 1)
                c1 = rng.randint(0, w - 4)
                c2 = rng.randint(c1 + 2, w - 1)
                # Check no overlap with prior rect perimeters
                collides = False
                for (pr1, pc1, pr2, pc2) in placed_rects:
                    # Rectangle overlap test (bbox intersection), with a one-cell
                    # moat so marker corners and output borders stay separated.
                    if not (r2 < pr1 - 1 or r1 > pr2 + 1
                            or c2 < pc1 - 1 or c1 > pc2 + 1):
                        collides = True
                        break
                if collides:
                    continue
                # Random diagonal: (r1, c1) & (r2, c2), OR (r1, c2) & (r2, c1)
                if rng.random() < 0.5:
                    g[r1][c1] = color
                    g[r2][c2] = color
                else:
                    g[r1][c2] = color
                    g[r2][c1] = color
                placed_rects.append((r1, c1, r2, c2))
                return True
            return False

        if not (_place_pair(2) and _place_pair(1)):
            continue
        # Sprinkle decoration cells in colors not in {0, 1, 2, 3, 8}
        decor_pool = [4, 5, 6, 7, 9]
        placed_decor = 0
        for _ in range(n_decor * 8):
            if placed_decor >= n_decor:
                break
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if g[r][c] != 0:
                continue
            # Check not inside a rect perimeter
            on_perimeter = False
            for (r1, c1, r2, c2) in placed_rects:
                if r1 <= r <= r2 and c1 <= c <= c2:
                    if r == r1 or r == r2 or c == c1 or c == c2:
                        on_perimeter = True
                        break
            if on_perimeter:
                continue
            g[r][c] = rng.choice(decor_pool)
            placed_decor += 1
        return g
    raise ValueError("could not place two separated marker rectangles")


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "only_one_cell":
        g[6][3] = 2
        g[6][7] = 1
        g[8][9] = 1
        return g
    if name == "three_cells":
        g[6][3] = 2
        g[8][5] = 2
        g[3][7] = 2
        g[6][7] = 1
        g[8][9] = 1
        return g
    if name == "cells_aligned":
        g[6][3] = 2
        g[6][8] = 2
        g[6][1] = 1
        g[8][9] = 1
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    msgs = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    if not (8 <= h <= 16 and 10 <= w <= 18):
        msgs.append("grid dimensions outside generated range")
    rects = []
    for color in (2, 1):
        cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]
        if len(cells) != 2:
            msgs.append(f"color {color} does not have exactly two markers")
            continue
        (r1, c1), (r2, c2) = cells
        if r1 == r2 or c1 == c2:
            msgs.append(f"color {color} markers are aligned, not diagonal rectangle corners")
            continue
        if abs(r1 - r2) < 2 or abs(c1 - c2) < 2:
            msgs.append(f"color {color} rectangle too small to expose an interior")
        rects.append((min(r1, r2), min(c1, c2), max(r1, r2), max(c1, c2)))
    if len(rects) == 2:
        a, b = rects
        if not (a[2] < b[0] - 1 or a[0] > b[2] + 1
                or a[3] < b[1] - 1 or a[1] > b[3] + 1):
            msgs.append("marker rectangles overlap or touch their one-cell moat")
    bad_decor = [v for row in grid for v in row if v in (3, 8)]
    if bad_decor:
        msgs.append("input uses output-only border colors 3/8")
    return msgs
