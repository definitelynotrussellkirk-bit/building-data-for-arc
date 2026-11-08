"""Generator for arc_additional_puzzles_21_set8:M55.

Sort objects by size and pack horizontally.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_rects,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_rects, all_same_size, all_touching.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect

GENERATOR_ID = "1756ff68b548"
# 1.2.0: was always 3 solid rects from a fixed 4-size pool; rule sorts ANY
#        objects by size then color, crops, hstacks. Now vary object count
#        2-5 and use random polyominoes (sized to keep distinct areas) for
#        more output shape/pattern diversity.
VERSION = "1.2.1"
TASK_ID = "1756ff68b548"
SUMMARY = "2-5 objects (varied shapes/sizes) in distinct colors, sorted by size then color and hstacked."

INVARIANTS = [
    "3 solid rectangles of distinct sizes",
    "rectangles use distinct colors",
    "rectangles don't touch (≥1 bg cell apart)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_rects", "all_same_size", "all_touching")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 12..16", "valid": "10..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_rects":        {"type": "int", "default": "3", "valid": "3..3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "three_distinct_size_rects",
                       "valid": "three_distinct_size_rects"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, at least one non-zero object cell present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in ("no_rects", "all_same_size", "all_touching"):
        return errs
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nonzero:
        errs.append("no object cells found")
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
        n_obj = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 15, 18)
        n_obj = None
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 13, 17)
        n_obj = None
    rng = ctx.draw_rng("layout")
    if n_obj is None:
        n_obj = rng.randint(3, 5) if difficulty == "hard" else rng.randint(2, 4)

    # Distinct target sizes (so sort-by-size has a clear signal); each
    # object is a random connected polyomino of that many cells.
    size_pool = [2, 3, 4, 5, 6, 7, 8]
    target_sizes = rng.sample(size_pool, min(n_obj, len(size_pool)))
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], len(target_sizes))

    g = full_grid(h, w, 0)
    occ = set()

    def _free(cells):
        for (r, c) in cells:
            if not (0 <= r < h and 0 <= c < w):
                return False
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if (r + dr, c + dc) in occ:
                        return False
        return True

    def _grow(size):
        cells = [(0, 0)]; seen = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(cells)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            nr, nc = r + dr, c + dc
            if (nr, nc) in seen:
                continue
            cells.append((nr, nc)); seen.add((nr, nc))
        rs = [x for x, _ in cells]; cs = [y for _, y in cells]
        mr, mc = min(rs), min(cs)
        return [(r - mr, c - mc) for r, c in cells]

    for size, color in zip(target_sizes, palette):
        poly = _grow(size)
        ph = max(r for r, _ in poly) + 1
        pw = max(c for _, c in poly) + 1
        for _ in range(80):
            r0 = rng.randint(1, h - ph - 1); c0 = rng.randint(1, w - pw - 1)
            abs_cells = [(r0 + r, c0 + c) for r, c in poly]
            if not _free(abs_cells):
                continue
            for (r, c) in abs_cells:
                g[r][c] = color
                occ.add((r, c))
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 14
    g = full_grid(h, w, 0)
    if name == "no_rects":
        # blank → no rectangles to sort
        return g
    if name == "all_same_size":
        # all rectangles same size → sort-by-size has no signal
        draw_rect(g, 1, 1, 2, 2, 4)
        draw_rect(g, 1, 5, 2, 2, 6)
        draw_rect(g, 1, 9, 2, 2, 7)
        return g
    if name == "all_touching":
        # rectangles touching → form a single component, can't sort separately
        draw_rect(g, 2, 2, 2, 2, 4)
        draw_rect(g, 2, 4, 2, 3, 6)
        draw_rect(g, 2, 7, 3, 3, 7)
        return g
    return g
