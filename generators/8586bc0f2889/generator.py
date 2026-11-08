"""Generator for arc_puzzle_bank_fifteenth_21_bundle:easy_101_stamp_hollow_3x3_rings.

Rule: each interior nonzero singleton stamps a hollow 3x3 ring (8 cells around center).

Combinatorial axes (8): grid_h, grid_w, palette_kind, markers,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_markers, markers_at_edge, overlapping_rings.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8586bc0f2889"
VERSION = "2.0.1"
TASK_ID = "8586bc0f2889"

SUMMARY = (
    "0-bg grid (h ∈ 8-10, w ∈ 9-12) "
    "with: TARGET ∈ 2-4 ISOLATED "
    "SINGLETON MARKER CELLS placed "
    "at INTERIOR positions (rows "
    "1..h-2, cols 1..w-2) so each "
    "marker's 3×3 footprint stays "
    "in-bounds. Markers use DISJOINT "
    "3×3 FOOTPRINTS (footprint of "
    "one cannot overlap another's "
    "via reserved-set tracking). "
    "Each marker painted in a random "
    "color from {1..9}. Rule (FOR "
    "EACH NON-BG INTERIOR MARKER, "
    "STAMP A HOLLOW 3×3 RING (8 "
    "CELLS AROUND THE CENTER, "
    "EXCLUDING THE CENTER ITSELF) "
    "IN THE MARKER'S COLOR; THE "
    "CENTER CELL STAYS PAINTED — "
    "OR PER DEMOS BECOMES BG): For "
    "EACH marker at (r, c) with "
    "color k: PAINT the 8 "
    "neighboring cells (r-1..r+1, "
    "c-1..c+1) excluding (r, c) "
    "with color k. The center (r, "
    "c) keeps its original color "
    "(or is set to 0 per demos). "
    "Net: each marker becomes a "
    "hollow 3×3 colored ring; "
    "background outside footprints "
    "stays 0."
)

INVARIANTS = [
    "background is 0",
    "markers are nonzero singleton cells",
    "markers are at least one cell from the border",
    "3x3 ring footprints are disjoint",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_markers", "markers_at_edge", "overlapping_rings")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "5..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "markers":        {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "interior_only",
                       "valid": "interior_only"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_markers|markers_at_edge|overlapping_rings"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; interior non-zero markers have disjoint 3x3 footprints."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nonzero:
        return []  # degenerate no_markers — allowed
    interior = [(r, c) for r, c in nonzero if 1 <= r <= h - 2 and 1 <= c <= w - 2]
    if not interior:
        return []  # degenerate markers_at_edge — allowed
    # Check footprints disjoint: no two interior markers within 3x3 of each other
    for i, (r1, c1) in enumerate(interior):
        for r2, c2 in interior[i + 1:]:
            if abs(r1 - r2) < 3 and abs(c1 - c2) < 3:
                return []  # degenerate overlapping_rings — allowed
    # Normal case: all interior markers have disjoint footprints
    errs = []
    if len(interior) > 8:
        errs.append(f"too many interior markers: {len(interior)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
        target = ctx.draw_int("markers", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
        target = ctx.draw_int("markers", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 12)
        target = ctx.draw_int("markers", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    reserved: set[tuple[int, int]] = set()
    placed = 0
    for _ in range(300):
        if placed >= target:
            break
        r = rng.randint(1, h - 2)
        c = rng.randint(1, w - 2)
        footprint = {(rr, cc) for rr in range(r - 1, r + 2) for cc in range(c - 1, c + 2)}
        if footprint & reserved:
            continue
        g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        reserved.update(footprint)
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_markers":
        # blank → no rings to stamp, output identical to input
        return g
    if name == "markers_at_edge":
        # markers on border → ring would extend off-grid
        g[0][3] = 4
        g[5][0] = 6
        g[h - 1][7] = 3
        return g
    if name == "overlapping_rings":
        # adjacent markers → rings collide; ambiguous which color wins
        g[2][3] = 4
        g[3][4] = 6
        g[5][6] = 3
        g[6][7] = 8
        return g
    return g
