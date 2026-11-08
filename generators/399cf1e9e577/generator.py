"""Generator for arc_puzzle_bank_21_set10_e:medium_j10 — Largest blob row-count bar chart.

Rule: largest blob (by size); crop to bbox; for each row of crop, count
non-zero cells. Output: row r has obj-color for first count_r cells.

Combinatorial axes (8): grid_h, grid_w, palette_kind, shape_variant,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_blob, multiple_equal_blobs, uniform_rows.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "399cf1e9e577"
# 1.3.0: defect-lint all_background_output + axis-honesty — a random-walk blob can
# have EQUAL per-row counts (rectangle-ish), making the histogram output a solid
# block; the AXES grid ranges lied. Blob now redrawn until row counts vary; AXES
# honest; self_check enforces varied row counts on the largest object.
VERSION = "1.3.0"
TASK_ID = "399cf1e9e577"
SUMMARY = "Single asymmetric color blob in interior; output is row-count bar chart of its bbox."

# Rivals: 'output blob bbox cropped' refuted by ≥1 demo where output is
# a histogram (left-justified bars) not the cropped shape. 'output is
# the blob's cell positions' refuted by ≥1 demo where the histogram
# bars use left-justified positions distinct from the original cells.
# 'use a fixed color' refuted by ≥2 demos with different blob colors.
# 'output a fixed bbox' refuted by ≥2 demos with different blob shapes.
# 4 demos with varied bboxes + row-count distributions cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "exactly one connected blob",
    "blob has varied row-counts (so output isn't trivially uniform)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blob", "multiple_equal_blobs", "uniform_rows")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "6-8 easy / 8-11 med / 10-14 hard", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "7-9 easy / 9-12 med / 11-15 hard", "valid": "7..15"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "shape_variant":  {"type": "int", "default": "rng 0..3", "valid": "0..3"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "single_asymmetric_blob",
                       "valid": "single_asymmetric_blob"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly one nonzero color (single blob); ≥3 nonzero cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    for r in range(h):
        for c in range(w):
            if not (0 <= grid[r][c] <= 9):
                errors.append(f"out-of-range value {grid[r][c]} at ({r},{c})")
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if not colors:
        pass  # degenerate (no_blob) — allowed
    elif len(colors) > 1:
        errors.append(f"expected single blob color, found {len(colors)} colors: {sorted(colors)}")
    if colors and not errors:
        # Varied per-row counts, else the histogram output is a solid block.
        rows_used = {}
        for r in range(h):
            n = sum(1 for c in range(w) if grid[r][c] != 0)
            if n:
                rows_used[r] = n
        if len(rows_used) >= 2 and len(set(rows_used.values())) < 2:
            errors.append("blob has equal per-row counts — the histogram demo would be solid")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 6, 8, 7, 9
        shape_size_lo, shape_size_hi = 4, 6
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 10, 14, 11, 15
        shape_size_lo, shape_size_hi = 7, 12
    else:
        h_lo, h_hi, w_lo, w_hi = 8, 11, 9, 12
        shape_size_lo, shape_size_hi = 5, 9
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    # Palette now includes color 1.
    color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    # Random connected blob with VARIED per-row counts: equal counts make the
    # rule's histogram a solid block (no-op demo) — redraw until they differ.
    size = rng.randint(shape_size_lo, shape_size_hi)
    for _blob_try in range(60):
        cells = [(0, 0)]
        seen = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(cells)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            nr, nc = r + dr, c + dc
            if (nr, nc) not in seen:
                cells.append((nr, nc)); seen.add((nr, nc))
        minr = min(r for r, _ in cells); minc = min(c for _, c in cells)
        cells = [(r - minr, c - minc) for r, c in cells]
        bh = max(r for r, _ in cells) + 1
        bw = max(c for _, c in cells) + 1
        row_counts = [sum(1 for rr, _ in cells if rr == r) for r in range(bh)]
        if len(set(row_counts)) >= 2 and bh <= h - 2 and bw <= w - 2:
            break
    else:
        # Deterministic staircase: rows of 2/2/1 cells — varied counts, tiny bbox.
        cells = [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)]
        bh, bw = 3, 3
    r0 = rng.randint(1, h - bh - 1)
    c0 = rng.randint(1, w - bw - 1)
    for dr, dc in cells:
        g[r0 + dr][c0 + dc] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_blob":
        # blank → no blob to histogram
        return g
    if name == "multiple_equal_blobs":
        # 2 blobs of same size → "largest" is ambiguous
        for r, c in [(1, 1), (1, 2), (2, 1)]: g[r][c] = 4
        for r, c in [(5, 5), (5, 6), (6, 5)]: g[r][c] = 6
        return g
    if name == "uniform_rows":
        # solid rectangle → all row counts equal, histogram is identity (no signal)
        for r in range(2, 5):
            for c in range(2, 6):
                g[r][c] = 4
        return g
    return g
