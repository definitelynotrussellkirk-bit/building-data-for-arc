"""Generator for arc_additional_puzzle_bank_volume3:M19 — Fill bbox of each color group.

Rule: for each non-bg color in the grid, find all cells of that color,
take their bbox, fill the bbox with that color in an empty output grid.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_colors,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: single_color, overlapping_bboxes, all_singletons.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1c50821f56a1"
VERSION = "1.1.1"
TASK_ID = "1c50821f56a1"
SUMMARY = "Scattered cells of 2-3 distinct colors; output fills the bbox of each color group."

INVARIANTS = [
    "between 2 and 3 distinct non-bg colors",
    "each color has 2..4 scattered cells",
    "color-bboxes don't overlap (so output isn't ambiguous)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("single_color", "overlapping_bboxes", "all_singletons")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "7..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_colors":       {"type": "int", "default": "rng 2..3",  "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "non_overlapping_bboxes",
                       "valid": "non_overlapping_bboxes"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _bboxes_overlap(bb1, bb2):
    return not (bb1[2] < bb2[0] or bb2[2] < bb1[0]
                or bb1[3] < bb2[1] or bb2[3] < bb1[1])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 8, 9)
        n_colors = ctx.draw_int("n_colors", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
        n_colors = ctx.draw_int("n_colors", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 6, 10)
        w = ctx.draw_int("grid_w", 8, 12)
        n_colors = ctx.draw_int("n_colors", 2, 3)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    colors = list(range(1, 10)); rng.shuffle(colors)
    bboxes = []
    used = set()
    for i in range(n_colors):
        for _ in range(20):
            rh = rng.randint(2, 4); rw = rng.randint(2, 4)
            r1 = rng.randint(0, h - rh); c1 = rng.randint(0, w - rw)
            bb = (r1, c1, r1 + rh - 1, c1 + rw - 1)
            if any(_bboxes_overlap(bb, ob) for ob in bboxes): continue
            n_cells = rng.randint(2, min(4, rh*rw))
            positions = [(r1 + dr, c1 + dc) for dr in range(rh) for dc in range(rw)]
            rng.shuffle(positions)
            corners = [(r1, c1), (r1, c1+rw-1), (r1+rh-1, c1), (r1+rh-1, c1+rw-1)]
            placed_corners = []
            for cr in corners:
                if g[cr[0]][cr[1]] == 0:
                    g[cr[0]][cr[1]] = colors[i]
                    used.add(cr)
                    placed_corners.append(cr)
                    if len(placed_corners) >= 2: break
            bboxes.append(bb)
            break
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: 2-3 distinct non-bg colors each with >=2 cells."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs = []
    from collections import Counter
    counts = Counter(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if len(counts) < 2:
        errs.append(f"expected 2-3 distinct colors, found {len(counts)}")
    sparse = [c for c, n in counts.items() if n < 2]
    if sparse:
        errs.append(f"colors with <2 cells: {sparse}")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "single_color":
        # only one color → output has just one bbox, weakly tests the rule
        g[1][1] = 4; g[1][3] = 4; g[3][2] = 4; g[3][4] = 4
        return g
    if name == "overlapping_bboxes":
        # two colors' bboxes overlap → output is ambiguous in the overlap
        g[1][1] = 4; g[3][4] = 4
        g[2][2] = 6; g[4][5] = 6
        return g
    if name == "all_singletons":
        # every color is a 1x1 bbox → fill is trivial (identity in output)
        g[1][2] = 4
        g[3][5] = 6
        g[5][7] = 3
        return g
    return g
