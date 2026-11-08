"""Generator for arc_puzzle_bank_21_set15_bundle:medium_o07 — corner key transforms biggest.

Rule: at(0,0) = key (a small int). Find the largest non-corner blob,
crop it to bbox, and apply a transform based on key.

Combinatorial axes (8): grid_h, grid_w, palette_kind, key,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_key, no_blob, square_blob.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "d62a0e470ae8"
VERSION = "2.1.0"  # output = single blob cropped + transformed by key at (0,0); blob 4-5 on tiny grid -> dup 39%. Widen grids + blob size (up to 10 cells) for more varied output crops.
TASK_ID = "d62a0e470ae8"
SUMMARY = (
    "0-bg grid (h~7-9, w~"
    "8-10) with: (a) CELL "
    "(0, 0) holds the KEY "
    "in {1..7} (a transform "
    "code); (b) ONE LARGEST "
    "NON-CORNER NON-"
    "RECTANGULAR BLOB of "
    "4-5 cells in a DISTINCT "
    "color (≠ key) at a "
    "random interior "
    "position. The blob is "
    "non-rectangular (bbox "
    "area > cell count) so "
    "transforms produce "
    "different shapes. "
    "Output uniq_out=30 "
    "(intrinsic — "
    "transformed crop "
    "normalizes by shape × "
    "key × color). Rule "
    "(TRANSFORM LARGEST "
    "BLOB BY CORNER KEY, "
    "CROP BBOX): READ KEY "
    "= g[0][0]. Find the "
    "LARGEST NON-CORNER "
    "BLOB. CROP to its "
    "BBOX. APPLY transform "
    "based on KEY (1..7 → "
    "different D4/rotation "
    "operations). EMIT the "
    "transformed crop. "
    "Net: corner key picks "
    "transform; largest "
    "blob is cropped and "
    "transformed."
)

INVARIANTS = [
    "background is 0",
    "(0,0) ∈ {1, 2, 3, 4, 5, 6, 7}",
    "exactly one large non-corner blob, strictly larger than any other blob",
    "blob is non-rectangular so transforms produce different shapes",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_key", "no_blob", "square_blob")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "6..13"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "key":            {"type": "int", "default": "rng 1..7", "valid": "1..7"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "key_corner_blob_body",
                       "valid": "key_corner_blob_body"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_key|no_blob|square_blob"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # output = the single blob cropped + transformed by the key at (0,0). Blob was
    # 4-5 cells on a tiny grid -> dup 39%. Widen grids + blob size for more varied crops.
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9); w = ctx.draw_int("grid_w", 8, 10); bsz = (4, 6)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 13); w = ctx.draw_int("grid_w", 11, 14); bsz = (7, 10)
    else:
        h = ctx.draw_int("grid_h", 8, 11); w = ctx.draw_int("grid_w", 9, 12); bsz = (5, 8)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    key = rng.randint(1, 7)
    g[0][0] = key
    used = {(0, 0)}
    color = rng.choice([c for c in [1, 2, 3, 4, 5, 6, 7, 8, 9] if c != key])
    for _ in range(40):
        cells = grow_blob(rng, h, w, used, rng.randint(*bsz), max_attempts=20)
        if cells is None:
            continue
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        bb = (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)
        if bb == len(cells):     # avoid solid rectangles (transform invisible)
            continue
        for r, c in cells:
            g[r][c] = color
        break
    return g


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    key = grid[0][0]
    if key not in range(1, 8):
        errs.append(f"corner key must be in 1..7, found {key}")
    blob_colors = {v for row in grid for v in row if v not in (0, key)}
    if len(blob_colors) != 1:
        errs.append(f"expected exactly one blob color distinct from key, found {sorted(blob_colors)}")
        return errs
    color = next(iter(blob_colors))
    comps = _components(grid, color)
    if len(comps) != 1:
        errs.append(f"expected one blob component, found {len(comps)}")
        return errs
    cells = comps[0]
    if (0, 0) in cells:
        errs.append("blob touches the corner key cell")
    if len(cells) < 4:
        errs.append(f"blob too small to teach a transform, size={len(cells)}")
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    bbox_area = (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)
    if bbox_area == len(cells):
        errs.append("blob is rectangular, making some transforms invisible")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_key":
        # blob without corner key → no transform dispatch defined
        for r, c in [(3, 3), (4, 3), (4, 4), (5, 4)]: g[r][c] = 4
        return g
    if name == "no_blob":
        # corner key alone, no blob → nothing to transform
        g[0][0] = 3
        return g
    if name == "square_blob":
        # blob is solid 2x2 square → all rotations/flips identical
        g[0][0] = 2
        for r in range(3, 5):
            for c in range(4, 6):
                g[r][c] = 4
        return g
    return g
