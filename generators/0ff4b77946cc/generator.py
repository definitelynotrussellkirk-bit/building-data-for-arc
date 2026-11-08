"""Generator for set12:E78 — Sort objects by size desc, pack horizontally with 1-col gaps.

Rule: sort objects by size desc, then h asc, then w asc, then color asc.
Output: pack sorted objects from left in their original orientation,
separated by 1-col gaps.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_shapes,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_objects, all_same_size, single_object.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.shape import RING_3X3
from puzzle_generators.helpers.place import place_no_overlap

GENERATOR_ID = "0ff4b77946cc"
# 2.3.0: reject/avoid source galleries whose canonical packed width would
# exceed the output canvas and silently clip later objects.
VERSION = "2.3.0"
TASK_ID = "0ff4b77946cc"
SUMMARY = (
    "0-bg grid (h ∈ 8-16, w ∈ 11-18, "
    "by difficulty) with: N_SHAPES ∈ "
    "3-4 OBJECTS drawn from _SHAPES "
    "bank (6 variants of sizes 1, 3, "
    "4, 5, 8, 9 — single cell, L, "
    "T-pentomino, ring 3×3, solid "
    "3×3), each with a DISTINCT "
    "SIZE drawn WITHOUT REPLACEMENT, "
    "each painted in a DISTINCT "
    "color from {1..9}, placed via "
    "place_no_overlap with 1-cell "
    "padding. Total packed width "
    "fits within w. Rule (SORT "
    "OBJECTS BY (SIZE DESC, BBOX-H "
    "ASC, BBOX-W ASC, COLOR ASC); "
    "PACK THEM HORIZONTALLY FROM "
    "THE LEFT WITH 1-COL BG GAPS, "
    "PRESERVING EACH OBJECT'S "
    "ORIGINAL SHAPE AND COLOR): "
    "EXTRACT every non-bg "
    "component. SORT by tuple "
    "(-cell_count, bbox_h, bbox_w, "
    "color). CROP each to its "
    "bbox. PACK left-to-right with "
    "1-COLUMN BG GAPS between, "
    "TOP-ALIGNED. Output height = "
    "max bbox height across all "
    "objects; width = sum_widths "
    "+ (n-1). Net: largest "
    "objects go first, "
    "left-aligned packing yields "
    "a sorted gallery."
)

INVARIANTS = [
    "3-4 connected objects of distinct sizes",
    "each object has a distinct color",
    "objects don't touch",
    "total packed width fits within w",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_objects", "all_same_size", "single_object")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 11..14", "valid": "10..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_shapes":       {"type": "int", "default": "rng 3..4", "valid": "2..6"},
    "palette_size":   {"type": "int", "default": "= n_shapes", "valid": "2..6"},
    "position_bias":  {"type": "str", "default": "scattered_distinct_sizes",
                       "valid": "scattered_distinct_sizes"},
    "n_distinct_colors": {"type": "int", "default": "= n_shapes", "valid": "2..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_SHAPES = [
    [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)],  # 9 solid 3x3
    RING_3X3,                                                                   # 8 ring
    [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)],                   # 7 stub
    [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)],                           # 6 2x3 block
    [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1)],                                   # 5 P
    [(0, 0), (0, 1), (0, 2), (0, 3)],                                          # 4 I-tetromino
    [(0, 0), (0, 1), (0, 2), (1, 1)],                                          # 4 T-tetromino
    [(0, 0), (0, 1), (1, 1)],                                                   # 3 L-tromino
    [(0, 0), (0, 1)],                                                           # 2 domino
    [(0, 0)],                                                                    # 1 dot
]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 11, 12)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 14, 18)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 11, 14)
    rng = ctx.draw_rng("layout")
    for _attempt in range(160):
        g = full_grid(h, w, 0)
        n_shapes = rng.randint(3, 4)
        sizes_pool = sorted({len(s) for s in _SHAPES}, reverse=True)
        chosen_sizes = sorted(rng.sample(sizes_pool, n_shapes), reverse=True)
        chosen_shapes = [rng.choice([s for s in _SHAPES if len(s) == sz])
                         for sz in chosen_sizes]
        if _packed_width_for_shapes(chosen_shapes) > w:
            continue
        palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_shapes)
        ok = True
        for i, shape in enumerate(chosen_shapes):
            if place_no_overlap(rng, g, shape, palette[i], padding=1, max_tries=120) is None:
                ok = False
                break
        if ok:
            return g
    # No silent underfill: deterministic 3-object fallback with distinct sizes.
    g = full_grid(h, w, 0)
    fallback = [([(0, 0)], 2, (1, 1)), ([(0, 0), (0, 1)], 4, (1, 4)),
                ([(0, 0), (0, 1), (1, 1)], 6, (4, 1))]
    for shape, color, (r0, c0) in fallback:
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = color
    return g


def _components_by_color(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                x, y = stack.pop(); cells.append((x, y))
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < h and 0 <= ny < w and (nx, ny) not in seen and grid[nx][ny] == color:
                        seen.add((nx, ny)); stack.append((nx, ny))
            comps.append((color, cells))
    return comps


def _bbox_width(cells):
    columns = [c for _r, c in cells]
    return max(columns) - min(columns) + 1


def _packed_width_for_shapes(shapes):
    return sum(_bbox_width(shape) for shape in shapes) + max(0, len(shapes) - 1)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    comps = _components_by_color(grid)
    errs = []
    if not (3 <= len(comps) <= 4):
        errs.append(f"expected 3-4 connected objects, found {len(comps)}")
    colors = [color for color, _ in comps]
    if len(colors) != len(set(colors)):
        errs.append("object colors must be distinct")
    sizes = [len(cells) for _, cells in comps]
    if len(sizes) != len(set(sizes)):
        errs.append("object sizes must be distinct for unambiguous primary sort")
    if comps:
        packed_width = _packed_width_for_shapes([cells for _color, cells in comps])
        if packed_width > len(grid[0]):
            errs.append(
                f"packed width {packed_width} exceeds output canvas width {len(grid[0])}"
            )
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 9, 12
    g = full_grid(h, w, 0)
    if name == "no_objects":
        # Empty grid — rule has nothing to sort or pack.
        return g
    if name == "all_same_size":
        # All objects are the same size — rule's primary sort key
        # (size desc) doesn't break ties, sort becomes ambiguous.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[1 + dr][1 + dc] = 4
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[5 + dr][6 + dc] = 6
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[1 + dr][8 + dc] = 7
        return g
    if name == "single_object":
        # Just one object — sort is trivial, no multi-object pack
        # evidence is shown.
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            g[3 + dr][4 + dc] = 5
        return g
    return g
