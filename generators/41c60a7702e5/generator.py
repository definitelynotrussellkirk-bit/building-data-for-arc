"""Generator for arc_puzzle_bank_21_set11_s:S11_M1 — Pick blob with most boundary cells.

Rule: sort objects by (boundary cells desc, size desc, color desc); pick
first; output empty + that blob recolored to 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_blobs, single_blob, tied_boundary.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "41c60a7702e5"
VERSION = "3.0.1"
TASK_ID = "41c60a7702e5"
SUMMARY = (
    "0-bg grid (h~8-10, w~11-14) with 2 SOLID "
    "RECTANGLES at hardcoded positions: (a) a "
    "2×7 RECTANGLE at (1, 1)..(2, 7) in one "
    "non-zero color; (b) a 4×4 RECTANGLE at "
    "(4, 4)..(7, 7) in another color. NOTE: "
    "currently both fixed sizes — diversity is "
    "intrinsic-low (only color permutations). "
    "Rule: for EACH BLOB (connected "
    "component), COMPUTE: (1) boundary cell "
    "count (cells with ≥1 bg/non-blob "
    "neighbor); (2) total size; (3) color. "
    "SORT blobs by (BOUNDARY DESC, SIZE DESC, "
    "COLOR DESC). SELECT the FIRST blob (max "
    "boundary). Output: an EMPTY GRID of the "
    "same dimensions with ONLY that selected "
    "blob, RECOLORED to COLOR 8 (cyan). All "
    "other blobs and bg are cleared. Net: "
    "input has multiple rectangles; output "
    "preserves only the one with most "
    "boundary cells, painted cyan."
)

INVARIANTS = [
    "between 2 and 3 non-touching solid rectangles",
    "boundary-cell counts are distinct",
    "blobs use distinct colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blobs", "single_blob", "tied_boundary")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 11..14", "valid": "9..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "2", "valid": "2..3"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "rects_distinct_boundaries",
                       "valid": "rects_distinct_boundaries"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _draw_rect(g, r1, c1, r2, c2, color):
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            g[r][c] = color


def _free(g, r0, c0, r1, c1):
    h, w = len(g), len(g[0])
    for r in range(r0 - 1, r1 + 2):
        for c in range(c0 - 1, c1 + 2):
            if 0 <= r < h and 0 <= c < w and g[r][c] != 0:
                return False
    return 0 <= r0 and 0 <= c0 and r1 < h and c1 < w


def _rand_shape(rng, maxh, maxw):
    """A solid rect of varied dims (boundary = perimeter, varies the winner)."""
    rh = rng.randint(1, maxh); rw = rng.randint(1, maxw)
    return [(r, c) for r in range(rh) for c in range(rw)]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: 2-3 non-touching solid rectangles in distinct colors."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    colors = set(grid[r][c] for r in range(h) for c in range(w)) - {0}
    if len(colors) < 1:
        errs.append("no non-bg rectangle cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10); w = ctx.draw_int("grid_w", 11, 13); nb = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14); w = ctx.draw_int("grid_w", 14, 18); nb = 4
    else:
        h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 12, 15); nb = 3
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    if difficulty == "medium" or difficulty is None:
        nb = rng.randint(2, 4)
    # several RANDOM-size solid rects (varied perimeters) -> the max-boundary
    # winner (output, recolored 8) varies in shape, not just grid size.
    palette = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], nb)
    for color in palette:
        cells = _rand_shape(rng, min(5, h - 2), min(7, w - 2))
        sh = max(r for r, _ in cells) + 1; sw = max(c for _, c in cells) + 1
        for _ in range(120):
            r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
            if _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1):
                for r, c in cells:
                    g[r0 + r][c0 + c] = color
                break
    return g
    palette = list(range(2, 10)); rng.shuffle(palette)
    _draw_rect(g, 1, 1, 2, 7, palette[0])
    _draw_rect(g, 4, 4, 7, 7, palette[1])
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 12
    g = full_grid(h, w, 0)
    if name == "no_blobs":
        # blank → no blobs to rank
        return g
    if name == "single_blob":
        # only 1 blob → trivially the "max-boundary" blob
        _draw_rect(g, 2, 2, 5, 5, 4)
        return g
    if name == "tied_boundary":
        # 2 rects with same boundary count → "max" is ambiguous (sort key tied at primary)
        _draw_rect(g, 1, 1, 3, 3, 4)   # 3x3, boundary 8
        _draw_rect(g, 5, 6, 7, 8, 6)   # 3x3, boundary 8 (tied)
        return g
    return g
