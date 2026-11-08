"""Generator for arc_puzzle_bank_tenth21:M68 — bbox row × col cross-product.

Rule: collect all blob bbox rows (every r covered by some bbox) and
bbox cols. Output paints 8 at every (r, c) where r is a bbox-row AND c
is a bbox-col.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_blobs, single_blob, overlapping_bboxes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "6387de413b52"
VERSION = "2.0.1"  # POISON: rule keys rows on COLOR-2 objects and cols on COLOR-3 objects, but gen placed RANDOM-colored blobs -> often no color-2/3 -> empty/near-empty output (canonical uses ONLY colors 0,2,3). Now place dedicated color-2 blobs (rows) + color-3 blobs (cols) at varied positions; output = their row x col cross-product in 8.
TASK_ID = "6387de413b52"
SUMMARY = (
    "0-bg grid with COLOR-2 blobs (whose bbox ROW ranges define the active "
    "rows) and COLOR-3 blobs (whose bbox COL ranges define the active cols). "
    "Rule: paint 8 at every (r,c) where r is in a color-2 bbox row-range AND c "
    "is in a color-3 bbox col-range. Output size == input size."
)

INVARIANTS = [
    "background is 0; only colors 0, 2, 3 appear",
    ">=1 color-2 blob (defines active rows) and >=1 color-3 blob (defines active cols)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blobs", "single_blob", "overlapping_bboxes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "disjoint_bboxes",
                       "valid": "disjoint_bboxes"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: only colors 0/2/3; ≥1 color-2 and ≥1 color-3 present (unless degenerate)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    all_vals = {grid[r][c] for r in range(h) for c in range(w)}
    bad = all_vals - {0, 2, 3}
    if bad:
        errs.append(f"unexpected colors (only 0/2/3 allowed): {sorted(bad)}")
    if 2 not in all_vals:
        errs.append("no color-2 blob (row-defining)")
    if 3 not in all_vals:
        errs.append("no color-3 blob (col-defining)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 11, 13)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 8, 11)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    used: set[tuple[int, int]] = set()

    def _place(color, count):
        placed = 0
        for _ in range(count):
            for _try in range(40):
                cells = grow_blob(rng, h, w, used, rng.randint(2, 4),
                                  max_attempts=20)
                if cells is None:
                    continue
                for r, c in cells:
                    g[r][c] = color
                used.update(cells)
                placed += 1
                break
        return placed

    # color-2 blobs define the active ROWS; color-3 blobs define the active COLS
    n2 = ctx.draw_int("n_row_blobs", 1, 3)
    n3 = ctx.draw_int("n_col_blobs", 1, 3)
    if _place(2, n2) == 0:
        g[0][0] = 2
    if _place(3, n3) == 0:
        g[h - 1][w - 1] = 3
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_blobs":
        # Empty grid — rule has no bboxes to compute the cross-product
        # over; output is empty.
        return g
    if name == "single_blob":
        # Only one blob — rule's cross-product is just the blob's bbox
        # interior; lacks the multi-blob signal the rule typifies.
        for r, c in [(2, 3), (2, 4), (3, 3)]: g[r][c] = 4
        return g
    if name == "overlapping_bboxes":
        # Two blobs whose bboxes share rows/cols — rule's cross-product
        # fires intersections; bbox-row sets overlap, defeating the
        # "disjoint bbox" invariant.
        for r, c in [(2, 2), (2, 3), (3, 2)]: g[r][c] = 4
        for r, c in [(2, 6), (3, 6), (3, 7)]: g[r][c] = 6
        return g
    return g
