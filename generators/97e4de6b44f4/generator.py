"""Generator for arc_puzzle_bank_twentyfirst21:M147 — marker-dispatched transform.

Rule: a marker (8 or 9) selects the transform: 8 → rotate-cw,
else → flip-lr. Apply to the (single) non-marker blob and crop.

Combinatorial axes (8): grid_h, grid_w, palette_kind, blob_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_marker, no_blob, rectangular_blob.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "97e4de6b44f4"
VERSION = "3.0.1"  # distinct=58/out_sh=3/dup40%: blob was only 3-4 cells so very few distinct non-rect shapes -> repeated transformed outputs. Use a random connected non-rectangular blob of 3-6 cells (varied bbox incl non-square) on a slightly larger grid -> output shape/content vary."
TASK_ID = "97e4de6b44f4"
SUMMARY = (
    "0-bg grid (h×w, ~4-6 by ~6-9) with: (a) one MARKER cell in "
    "color 8 (cyan) or 9 (maroon) placed at the top of the grid; "
    "(b) one connected non-rectangular BLOB of 3-4 cells in some "
    "color ≠ {0, 8, 9}, placed below the marker. Rule: detect "
    "marker color. Extract blob, crop to bbox. If marker == 8, "
    "apply rotate-cw; else (marker == 9), apply flip-lr. Output "
    "= transformed cropped blob."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly one marker cell in {8, 9}",
    "exactly one connected blob (3-4 cells), color ∉ {0, 8, 9}",
    "blob is non-rectangular (transforms produce visibly different output)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "no_blob", "rectangular_blob")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 4..6", "valid": "3..10"},
    "grid_w":         {"type": "int", "default": "rng 6..9", "valid": "5..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "blob_size":      {"type": "int", "default": "rng 3..4", "valid": "2..6"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "marker_top_blob_below",
                       "valid": "marker_top_blob_below"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly 1 marker cell in {8,9}; ≥1 non-{0,8,9} cell (the blob)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    markers = [(r, c) for r in range(h) for c in range(w) if grid[r][c] in (8, 9)]
    blobs = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 8, 9)]
    errs = []
    if len(markers) != 1:
        errs.append(f"expected exactly 1 marker in {{8,9}}; found {len(markers)}")
    if not blobs:
        errs.append("no non-{0,8,9} blob cells")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 4, 5); w = ctx.draw_int("grid_w", 6, 7)
        k_lo, k_hi = 3, 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 6, 8); w = ctx.draw_int("grid_w", 9, 11)
        k_lo, k_hi = 4, 6
    else:
        h = ctx.draw_int("grid_h", 5, 7); w = ctx.draw_int("grid_w", 7, 10)
        k_lo, k_hi = 3, 6
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    marker = rng.choice([8, 9])
    g[0][rng.randint(w // 2, w - 1)] = marker
    color = rng.choice([1, 2, 3, 4, 5, 6, 7])
    # Random connected NON-rectangular blob (so rotate-cw vs flip-lr differ),
    # placed below the marker row.
    for _ in range(60):
        shape = _rand_poly(rng, rng.randint(k_lo, k_hi))
        sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
        if sh * sw == len(shape):          # rectangular -> skip
            continue
        if sh > h - 1 or sw > w:
            continue
        r0 = rng.randint(1, h - sh); c0 = rng.randint(0, w - sw)
        if any(g[r0 + dr][c0 + dc] != 0 for dr, dc in shape):
            continue
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = color
        break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 5, 7
    g = full_grid(h, w, 0)
    if name == "no_marker":
        # blob without 8/9 marker → no transform dispatch, undefined rule
        for r, c in [(2, 2), (3, 2), (3, 3)]:
            g[r][c] = 4
        return g
    if name == "no_blob":
        # marker alone, no payload to transform
        g[0][5] = 8
        return g
    if name == "rectangular_blob":
        # solid 2x2 blob → both rotate-cw and flip-lr produce same output
        g[0][5] = 8
        for r in range(2, 4):
            for c in range(2, 4):
                g[r][c] = 4
        return g
    return g
