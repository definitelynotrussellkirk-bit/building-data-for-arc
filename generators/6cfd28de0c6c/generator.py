"""Generator for arc_additional_puzzle_bank_volume8:E54 — crop to non-zero bbox.

Rule: find the bbox of all non-zero cells. Output is the subgrid of
that bbox (preserving original cell values, including 0-padding
within the bbox interior).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6cfd28de0c6c"
VERSION = "1.2.1"
TASK_ID = "6cfd28de0c6c"
SUMMARY = (
    "Several non-zero cells (in various colors) scattered on a 0-bg "
    "grid with non-zero padding on every side. Rule outputs the "
    "subgrid bounded by the bbox of all non-zero cells, preserving "
    "interior 0-cells within the bbox."
)

# Rivals: 'output is input' refuted by any demo (output is smaller).
# 'output is content cells only' refuted by demos with internal 0s
# that are preserved. 'recolor to single color' refuted by demos
# preserving original colors. 'crop to single non-zero only' refuted
# by demos with multiple scattered cells producing a larger bbox.
# 3 demos with varied scatter patterns cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥2 non-zero cells whose bbox is strictly smaller than the grid",
    "≥1 cell of padding on EVERY side of the bbox",
]

AXES = {
    "grid_h":     {"type": "int", "default": "rng 9..13", "valid": "8..18"},
    "grid_w":     {"type": "int", "default": "rng 9..13", "valid": "8..18"},
    "n_cells":    {"type": "int", "default": "rng 4..10", "valid": "2..20"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥2 non-zero cells; bbox strictly inside grid (1-cell padding every side)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if len(nonzero) < 2:
        errs.append(f"fewer than 2 non-zero cells: {len(nonzero)}")
        return errs
    r1 = min(r for r, c in nonzero); r2 = max(r for r, c in nonzero)
    c1 = min(c for r, c in nonzero); c2 = max(c for r, c in nonzero)
    if r1 < 1:
        errs.append(f"no top padding: bbox starts at row {r1}")
    if r2 > h - 2:
        errs.append(f"no bottom padding: bbox ends at row {r2} of {h}")
    if c1 < 1:
        errs.append(f"no left padding: bbox starts at col {c1}")
    if c2 > w - 2:
        errs.append(f"no right padding: bbox ends at col {c2} of {w}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = rng.randint(8, 10); w = rng.randint(8, 10)
        n_cells = rng.randint(3, 6)
    elif difficulty == "hard":
        h = rng.randint(14, 20); w = rng.randint(14, 20)
        n_cells = rng.randint(10, 20)
    else:
        h = rng.randint(10, 14); w = rng.randint(10, 14)
        n_cells = rng.randint(5, 12)

    # Pick a bbox with at least 1-cell padding on every side.
    bbox_r1 = rng.randint(1, h - 4)
    bbox_r2 = rng.randint(bbox_r1 + 2, h - 2)
    bbox_c1 = rng.randint(1, w - 4)
    bbox_c2 = rng.randint(bbox_c1 + 2, w - 2)

    g = full_grid(h, w, 0)
    # Fill scattered cells within the bbox; ensure ALL 4 corners of the
    # bbox have at least one non-zero cell on each edge (so bbox of
    # filled cells = our chosen bbox exactly).
    palette_pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(palette_pool)
    palette = palette_pool[:rng.randint(2, 6)]
    # Edge anchors
    g[bbox_r1][rng.randint(bbox_c1, bbox_c2)] = rng.choice(palette)
    g[bbox_r2][rng.randint(bbox_c1, bbox_c2)] = rng.choice(palette)
    g[rng.randint(bbox_r1, bbox_r2)][bbox_c1] = rng.choice(palette)
    g[rng.randint(bbox_r1, bbox_r2)][bbox_c2] = rng.choice(palette)
    interior = [(r, c) for r in range(bbox_r1, bbox_r2 + 1)
                for c in range(bbox_c1, bbox_c2 + 1)]
    rng.shuffle(interior)
    placed = sum(1 for r, c in interior if g[r][c] != 0)
    for r, c in interior:
        if placed >= n_cells:
            break
        if g[r][c] != 0:
            continue
        g[r][c] = rng.choice(palette)
        placed += 1
    return g
