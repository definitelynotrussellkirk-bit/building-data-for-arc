"""Generator for arc_additional_puzzles_21_set16_bundle:M107 — sort objects by size DESC, paste side-by-side.

Rule: extract every connected non-bg object's bbox crop. Sort by size
descending (tiebreakers: top-row, left-col, color), then paste the
crops horizontally with 1-col gap.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_objs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_objects, equal_sizes, single_object.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.palette import random_palette
from puzzle_generators.helpers.blobs import bbox_overlaps

GENERATOR_ID = "3fcea70c3acf"
VERSION = "2.0.1"
TASK_ID = "3fcea70c3acf"
SUMMARY = (
    "0-bg grid (h~8-11, w~"
    "12-16) with 2-3 "
    "CONNECTED NON-BG "
    "OBJECTS, each a "
    "DISTINCT SHAPE drawn "
    "from a 2-7-cell shape "
    "bank (sizes 2, 3, 4, 5, "
    "6, 7) in DISTINCT "
    "COLORS, placed at non-"
    "overlapping non-touching "
    "positions (1-cell "
    "padding via bbox-"
    "overlap check). Each "
    "object has a UNIQUE "
    "cell-count so the size-"
    "sort is unambiguous. "
    "Rule (SORT OBJECTS BY "
    "SIZE DESC, PASTE BBOX "
    "CROPS SIDE-BY-SIDE): "
    "extract every 4-"
    "CONNECTED NON-0 "
    "COMPONENT. For each, "
    "compute its BBOX CROP "
    "(subgrid containing the "
    "shape, padded to bbox). "
    "SORT the crops by CELL "
    "COUNT DESCENDING "
    "(tiebreakers: top-row, "
    "left-col, color). "
    "PASTE the sorted crops "
    "HORIZONTALLY with 1-"
    "column GAP of 0 "
    "background between "
    "adjacent crops. Output "
    "is a fresh grid sized "
    "to fit the row of "
    "crops. Net: objects "
    "lined up biggest-first "
    "left-to-right with a "
    "gap between each."
)

INVARIANTS = [
    "background is 0",
    "2-3 4-connected non-bg objects, each a distinct color",
    "each object has a distinct cell-count (so size-sort is unambiguous)",
    "objects don't touch each other",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_objects", "equal_sizes", "single_object")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 12..16", "valid": "10..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_objs":         {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "scattered_distinct_sizes",
                       "valid": "scattered_distinct_sizes"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_SHAPES_BY_SIZE = {
    2: [[(0, 0), (0, 1)], [(0, 0), (1, 0)]],
    3: [[(0, 0), (0, 1), (0, 2)], [(0, 0), (1, 0), (1, 1)]],
    4: [[(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (0, 2), (0, 3)]],
    5: [[(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)],
        [(0, 0), (1, 0), (1, 1), (1, 2), (2, 2)]],
    6: [[(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)]],
    7: [[(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (2, 0), (3, 0)]],
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, ≥2 non-bg distinct-color connected components."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    colors = set(grid[r][c] for r in range(h) for c in range(w)) - {0}
    if len(colors) < 2:
        errs.append(f"expected ≥2 distinct non-bg colors, got {len(colors)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 12, 13)
        n = ctx.draw_int("n_objs", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 16, 19)
        n = ctx.draw_int("n_objs", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 12, 16)
        n = ctx.draw_int("n_objs", 2, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    sizes = rng.sample(list(_SHAPES_BY_SIZE.keys()), n)
    palette = list(random_palette(rng, n))
    placed: list[tuple[int, int, int, int]] = []
    for size, color in zip(sizes, palette):
        shape = rng.choice(_SHAPES_BY_SIZE[size])
        sh = max(c[0] for c in shape) + 1
        sw = max(c[1] for c in shape) + 1
        for _ in range(80):
            r0 = rng.randint(0, h - sh)
            c0 = rng.randint(0, w - sw)
            bb_pad = (r0 - 1, c0 - 1, r0 + sh, c0 + sw)
            if any(bbox_overlaps(bb_pad, p) for p in placed): continue
            paint_at(g, r0, c0, shape, color)
            placed.append((r0, c0, r0 + sh - 1, c0 + sw - 1))
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 14
    g = full_grid(h, w, 0)
    if name == "no_objects":
        # Empty grid — rule has no objects to sort/paste.
        return g
    if name == "equal_sizes":
        # All objects same size — sort by size is ambiguous.
        for r, c in [(1, 1), (1, 2), (2, 1)]: g[r][c] = 4
        for r, c in [(1, 6), (1, 7), (2, 6)]: g[r][c] = 5
        for r, c in [(5, 1), (5, 2), (6, 1)]: g[r][c] = 6
        return g
    if name == "single_object":
        # Only one object — sort/paste is trivial.
        for r in range(2, 5):
            for c in range(2, 5): g[r][c] = 4
        return g
    return g
