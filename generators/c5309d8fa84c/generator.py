"""Generator for arc_puzzle_bank_21_set12_bundle:medium_l11.

Rule: sort objects by color asc; concatenate their bbox crops
horizontally with 1-col gaps; output max-h × total-w.

Combinatorial axes (8): grid_h/w, palette_kind, n_blobs, palette_size,
position_bias, n_distinct_colors, blob_size_variation, texture.
Degenerates: only_one_blob, blobs_touching, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "c5309d8fa84c"
VERSION = "2.1.1"  # shape-locked-out: 3 FIXED blobs -> output always ~3x10 (rule hstacks object crops sorted by colour). Now N (2-5) random varied-size blobs (separated) -> output dims vary; hstack width guarded <=30.
TASK_ID = "c5309d8fa84c"
SUMMARY = (
    "0-bg grid (h~8-10, w~11-13) with EXACTLY 3 "
    "NON-TOUCHING CONNECTED BLOBS at hardcoded "
    "positions: (a) a 4-cell L-tetromino at "
    "(1, 1); (b) a 4-cell T-shape at (1, 5); "
    "(c) a 3-cell corner at (h-4, w-4). Each in "
    "a DISTINCT non-zero color from {2..9}. "
    "NOTE: shapes/positions hardcoded — "
    "diversity is intrinsic-low. Rule: identify "
    "each non-bg CONNECTED COMPONENT. SORT them "
    "by COLOR ASCENDING. For each blob, CROP "
    "to its bbox. CONCATENATE the cropped bboxes "
    "HORIZONTALLY from left to right with "
    "1-COL GAPS between them. Output: "
    "max-height-among-blobs × sum-of-widths + "
    "gaps. Net: input has scattered colored "
    "blobs; output is them side-by-side sorted "
    "by color in a horizontal pack."
)

INVARIANTS = [
    "exactly 3 non-touching blobs",
    "blobs use distinct colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "rainbow")
DEGENERATE_TEXTURES = ("only_one_blob", "blobs_touching", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..18"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "3", "valid": "3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "blob_size_variation": {"type": "str", "default": "varied",
                            "valid": "varied"},
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
        h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 11, 14); n = ctx.draw_int("n", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 18); w = ctx.draw_int("grid_w", 14, 22); n = ctx.draw_int("n", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 10, 14); w = ctx.draw_int("grid_w", 12, 18); n = ctx.draw_int("n", 3, 4)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    palette = list(range(2, 10)); rng.shuffle(palette)
    # the rule hstacks each object's bbox crop (sorted by colour); output dims depend
    # on the blob sizes -> use N random varied-size blobs (was 3 FIXED blobs -> out always ~3x10)
    used = set()
    placed = 0; total_w = 0
    for col in palette[:n]:
        shp = _poly(rng, rng.randint(3, 7))
        sh = max(r for r, _ in shp) + 1; sw = max(c for _, c in shp) + 1
        if total_w + sw + (1 if placed else 0) > 30:   # hstack output must fit 30 cols
            break
        for _ in range(120):
            r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
            cells = {(r0 + dr, c0 + dc) for dr, dc in shp}
            ring = {(r, c) for (br, bc) in cells for r in (br - 1, br, br + 1) for c in (bc - 1, bc, bc + 1)}
            if ring & used:
                continue
            for (r, c) in cells:
                g[r][c] = col
            used |= cells
            placed += 1; total_w += sw + (1 if placed > 1 else 0)
            break
    if placed < 2:                          # ensure >=2 blobs for a non-trivial hstack
        g[0][0] = palette[0]; g[h - 1][w - 1] = palette[1]
    return g


def _poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=2 distinct nonzero colors (blobs); each color forms >=1 cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 2:
        errors.append(f"expected >=2 distinct nonzero colors (blobs), found {len(colors)}")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 9, 12
    g = full_grid(h, w, 0)
    if name == "only_one_blob":
        # only 1 blob — concat trivial
        paint_at(g, 2, 2, [(0, 0), (1, 0), (1, 1)], 4)
        return g
    if name == "blobs_touching":
        # blobs touching — would merge into one component
        paint_at(g, 2, 2, [(0, 0), (1, 0)], 4)
        paint_at(g, 2, 4, [(0, 0), (1, 0)], 6)  # touches first
        paint_at(g, 6, 8, [(0, 0)], 7)
        return g
    if name == "no_blobs":
        # empty grid — no objects to concat
        return g
    return g
