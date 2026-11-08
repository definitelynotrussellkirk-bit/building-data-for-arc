"""Generator for arc_puzzle_bank_21_set15_bundle:medium_o03 — recolor by nearest border.

Rule: each blob gets recolored by its nearest border (top→1, bottom→2,
left→3, right→4). Ties keep the original color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_blobs, all_centered, blob_at_corner.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "cdaa7a006471"
VERSION = "2.0.1"
TASK_ID = "cdaa7a006471"
SUMMARY = (
    "0-bg grid (h ∈ 9-11, w ∈ 11-13) "
    "with: N ∈ 3-4 DISTINCT-COLOR "
    "BLOBS, each a 3-5 cell "
    "irregular blob built via "
    "grow_blob random walk, painted "
    "in DISTINCT colors drawn from "
    "{5,6,7,8,9}, placed at non-"
    "overlapping positions where "
    "each blob has a STRICTLY "
    "NEAREST border (no tie among "
    "top, bottom, left, right) — "
    "_nearest_unique check enforces "
    "this. Rule (FOR EACH BLOB, "
    "COMPUTE THE DISTANCE FROM ITS "
    "BBOX TO EACH OF THE 4 GRID "
    "BORDERS (TOP, BOTTOM, LEFT, "
    "RIGHT); RECOLOR THE BLOB BY "
    "THE NEAREST BORDER: TOP→COLOR "
    "1, BOTTOM→COLOR 2, LEFT→COLOR "
    "3, RIGHT→COLOR 4; TIES KEEP "
    "ORIGINAL COLOR): For EACH "
    "blob with bbox (r1, c1, r2, "
    "c2): COMPUTE distances "
    "(r1, h-1-r2, c1, w-1-c2). "
    "FIND the UNIQUE minimum "
    "(top=0, bottom=1, left=2, "
    "right=3). RECOLOR every "
    "cell of the blob by that "
    "border index (0→1, 1→2, "
    "2→3, 3→4). On tie: keep "
    "original color. Net: blobs "
    "recolored by which grid "
    "border is closest."
)

INVARIANTS = [
    "background is 0",
    "each blob has a strictly nearest border (no tie among the 4 sides)",
    "blobs have distinct colors",
    "blobs aren't 4-touching",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blobs", "all_centered", "blob_at_corner")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_blobs":        {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "blobs_with_unique_nearest_border",
                       "valid": "blobs_with_unique_nearest_border"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_blobs|all_centered|blob_at_corner"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; all values 0-9; all non-zero cells are in 'high' colors (5-9 per SUMMARY)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(v < 0 or v > 9 for row in grid for v in row):
        errs.append("cell value out of 0-9")
    return errs


def _nearest_unique(cells, h, w):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r1, r2 = min(rs), max(rs)
    c1, c2 = min(cs), max(cs)
    dists = [r1, h - 1 - r2, c1, w - 1 - c2]
    m = min(dists)
    return dists.count(m) == 1


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
        n = ctx.draw_int("n_blobs", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 12, 13)
        n = ctx.draw_int("n_blobs", 4, 4)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 13)
        n = ctx.draw_int("n_blobs", 3, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    palette = rng.sample([5, 6, 7, 8, 9], n)
    used: set[tuple[int, int]] = set()
    for color in palette:
        for _ in range(60):
            cells = grow_blob(rng, h, w, used, rng.randint(3, 5), max_attempts=20)
            if cells is None:
                continue
            if not _nearest_unique(cells, h, w):
                continue
            for r, c in cells:
                g[r][c] = color
            used |= cells
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_blobs":
        # blank → no blobs to recolor
        return g
    if name == "all_centered":
        # blob at exact center → all 4 borders equidistant, no unique nearest
        for r in range(4, 6):
            for c in range(5, 7): g[r][c] = 5
        return g
    if name == "blob_at_corner":
        # blob touches 2 borders simultaneously → 2 nearest borders tied
        g[0][0] = 5; g[0][1] = 5; g[1][0] = 5
        return g
    return g
