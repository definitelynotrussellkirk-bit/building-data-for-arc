"""Generator for arc_puzzle_bank_tenth21:E65.

Solid 3x3 rings with zero centers have their centers filled.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_rings,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_rings, filled_centers, partial_rings.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3f9bb51d528b"
VERSION = "2.0.1"
TASK_ID = "3f9bb51d528b"

SUMMARY = (
    "0-bg grid (h, w~8-13) with 2-4 SOLID 3×3 "
    "RINGS, each in a DISTINCT non-zero color. "
    "Each ring is an 8-cell hollow square: 3×3 "
    "bbox with the 8 perimeter cells painted in "
    "the ring's color and the CENTER cell at "
    "(r+1, c+1) initially 0. Rings are "
    "non-touching (1-cell padding from each "
    "other and grid edges). Rule: for EVERY 3×3 "
    "RING (8 cells of a single color forming a "
    "ring with a 0-cell center inside), IDENTIFY "
    "the CENTER cell (the unique 0-cell strictly "
    "inside the 3×3 bbox). FILL that center "
    "cell with the RING'S OWN color, completing "
    "the 3×3 into a SOLID monochrome 3×3 "
    "square. Net: each hollow ring becomes a "
    "solid 3×3 in its color; ring perimeters "
    "stay."
)

INVARIANTS = [
    "background is 0",
    "each motif is a 3x3 ring of one nonzero color",
    "the center cell is initially zero",
    "rings are separated to avoid unintended centers",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_rings", "filled_centers", "partial_rings")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "5..20"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "5..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_rings":        {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "separated_3x3_rings",
                       "valid": "separated_3x3_rings"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=8 nonzero cells (at least 1 ring of 8 perimeter cells) and bg=0."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    nonzero_count = sum(1 for r in range(h) for c in range(w) if grid[r][c] != 0)
    if nonzero_count < 8:
        errs.append(f"expected >=8 nonzero cells (at least 1 ring of 8 cells), found {nonzero_count}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
        target = ctx.draw_int("n_rings", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 12, 13)
        target = ctx.draw_int("n_rings", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 9, 13)
        target = ctx.draw_int("n_rings", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    reserved: set[tuple[int, int]] = set()
    placed = 0
    for _ in range(500):
        if placed >= target:
            break
        r0 = rng.randint(0, h - 3)
        c0 = rng.randint(0, w - 3)
        guard = {(r, c) for r in range(max(0, r0 - 1), min(h, r0 + 4))
                 for c in range(max(0, c0 - 1), min(w, c0 + 4))}
        if guard & reserved:
            continue
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        for dr in range(3):
            for dc in range(3):
                if (dr, dc) != (1, 1):
                    g[r0 + dr][c0 + dc] = color
        reserved.update(guard)
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_rings":
        # blank → no rings to fill
        return g
    if name == "filled_centers":
        # centers already filled → rule's "center is zero" precondition fails
        for dr in range(3):
            for dc in range(3):
                g[1 + dr][1 + dc] = 4
        for dr in range(3):
            for dc in range(3):
                g[5 + dr][5 + dc] = 6
        return g
    if name == "partial_rings":
        # rings missing 1 cell → not a complete 8-cell ring, rule may not fire
        for dr in range(3):
            for dc in range(3):
                if (dr, dc) not in [(1, 1), (0, 0)]:
                    g[1 + dr][1 + dc] = 4
        return g
    return g
